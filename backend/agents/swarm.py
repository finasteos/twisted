"""
SwarmOrchestrator: Multi-agent debate and consensus formation.
Coordinates 6 specialized agents through structured debate rounds.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from backend.agents.base_agent import BaseAgent
from backend.agents.context_weaver.agent import ContextWeaverAgent
from backend.agents.outcome_architect.agent import OutcomeArchitectAgent
from backend.agents.echo_vault.agent import EchoVaultAgent
from backend.agents.chronicle_scribe.agent import ChronicleScribeAgent
from backend.agents.pulse_monitor.agent import PulseMonitorAgent
from backend.agents.dispute_skeptic.agent import DisputeSkepticAgent
from backend.agents.debate_engine import DebateEngine
from backend.llm.hybrid_router import HybridLLMRouter


@dataclass
class DebateRound:
    round_number: int
    agent_outputs: Dict[str, Dict]
    consensus_reached: bool
    convergence_score: float


class SwarmOrchestrator:
    """
    Orchestrates multi-agent debate for optimal outcome determination.

    Debate Protocol:
    1. Context Weaver analyzes situation → vector store
    2. Outcome Architect generates scenarios
    3. Debate rounds: agents challenge/support/synthesize
    4. Convergence detection: confidence > 0.8, agreement > 3 agents
    5. Chronicle Scribe generates final deliverables
    """

    CONVERGENCE_THRESHOLD = 0.80
    MIN_AGREEMENT_COUNT = 3
    MAX_DEBATE_ROUNDS = 5

    def __init__(
        self,
        gemini_wrapper,
        chroma_manager,
        connection_manager,
        hybrid_router=None,
        tool_registry=None,
    ):
        self.llm = gemini_wrapper
        self.memory = chroma_manager
        self.comm = connection_manager
        self.router = hybrid_router
        self.tool_registry = tool_registry

        self.agents: Dict[str, BaseAgent] = {}
        self.debate_history: List[DebateRound] = []
        self.debate_engine = DebateEngine(self.llm) if self.llm else None

    async def initialize(self):
        """Initialize all agents with dependencies."""
        self.agents = {
            "context_weaver": ContextWeaverAgent(self.llm, self.memory, self.comm),
            "outcome_architect": OutcomeArchitectAgent(
                self.llm, self.memory, self.comm
            ),
            "echo_vault": EchoVaultAgent(self.llm, self.memory, self.comm),
            "chronicle_scribe": ChronicleScribeAgent(self.llm, self.memory),
            "pulse_monitor": PulseMonitorAgent(self.llm, self.memory, self.comm),
            "dispute_skeptic": DisputeSkepticAgent(self.llm, self.memory, self.comm),
        }

    async def run_context_analysis(
        self, case_id: str, progress_callback: Callable, thought_callback: Callable
    ):
        """Stage 1: Context Weaver builds situation understanding."""
        context_agent = self.agents["context_weaver"]

        # Query raw ingestion data
        raw_docs = await self.memory.query(
            collection="case_ingestion",
            query_texts=["entities people organizations dates"],
            where={"case_id": case_id},
            n_results=20,
        )

        # Analyze and extract structured context
        analysis = await context_agent.analyze(
            case_id=case_id, documents=raw_docs, thought_callback=thought_callback
        )

        # Store structured analysis
        await self.memory.store_analysis(
            case_id=case_id,
            entities=analysis["entities"],
            relationships=analysis["relationships"],
            timeline=analysis["timeline"],
            risk_flags=analysis["risk_flags"],
        )

        await progress_callback(100, "Context analysis complete")

    async def run_debate(
        self,
        case_id: str,
        rounds: int = 3,
        progress_callback: Callable = None,
        thought_callback: Callable = None,
        log_callback: Callable = None,
    ) -> Dict:
        """
        Stage 2-4: Multi-agent debate for outcome optimization.

        Debate Structure:
        - Round 1: Outcome Architect presents scenarios
        - Round 2: Context Weaver challenges/validates assumptions
        - Round 3+: Synthesis and convergence detection
        """

        # Initialize debate
        await log_callback(
            case_id=case_id,
            level="INFO",
            agent="Coordinator",
            message="Initiating swarm debate for outcome optimization",
        )

        # Round 1: Generate scenarios
        outcome_agent = self.agents["outcome_architect"]
        scenarios = await outcome_agent.generate_scenarios(
            case_id=case_id, thought_callback=thought_callback
        )

        await log_callback(
            case_id=case_id,
            level="DEBATE",
            agent="Outcome Architect",
            message=f"Generated {len(scenarios)} outcome scenarios",
            metadata={"scenarios": [s["name"] for s in scenarios]},
        )

        # Debate rounds
        veto_count = 0
        for round_num in range(1, rounds + 1):
            await log_callback(
                case_id=case_id,
                level="DEBATE",
                agent="Coordinator",
                message=f"Debate Round {round_num} beginning",
            )

            # Collect agent analyses
            agent_outputs = {}

            # Context Weaver validates scenario assumptions
            context_analysis = await self.agents["context_weaver"].validate_scenarios(
                case_id=case_id, scenarios=scenarios, thought_callback=thought_callback
            )
            agent_outputs["context_weaver"] = context_analysis

            # Outcome Architect revises based on challenges
            revised_scenarios = await outcome_agent.revise_scenarios(
                scenarios=scenarios,
                challenges=context_analysis.get("challenges", []),
                thought_callback=thought_callback,
            )
            agent_outputs["outcome_architect"] = {
                "scenarios": revised_scenarios,
                "confidence": self._calculate_scenario_confidence(revised_scenarios),
            }

            # Dispute Skeptic adversarial review (Red Team)
            skeptic_analysis = await self.agents[
                "dispute_skeptic"
            ].analyze_and_challenge(
                case_id=case_id,
                scenarios=revised_scenarios,
                thought_callback=thought_callback,
            )
            agent_outputs["dispute_skeptic"] = skeptic_analysis

            if skeptic_analysis.get("consensus_veto"):
                veto_count += 1
                await log_callback(
                    case_id=case_id,
                    level="WARNING",
                    agent="Dispute Skeptic",
                    message=f"CONSENSUS VETOED: {skeptic_analysis.get('challenges', ['Unspecified risk'])[0]}",
                    metadata={"veto_count": veto_count},
                )

            # Check convergence
            convergence = self._check_convergence(agent_outputs)

            # If vetoed too many times, Coordinator overrides to force "Disputed Consensus"
            if veto_count >= 2 and not convergence["consensus"]:
                await log_callback(
                    case_id=case_id,
                    level="CAUTION",
                    agent="Coordinator",
                    message='MAX VETOES REACHED: Forcing "Disputed Consensus" for human review.',
                )
                convergence["consensus"] = True
                convergence["disputed"] = True

            debate_round = DebateRound(
                round_number=round_num,
                agent_outputs=agent_outputs,
                consensus_reached=convergence["consensus"],
                convergence_score=convergence["score"],
            )
            self.debate_history.append(debate_round)

            await log_callback(
                case_id=case_id,
                level="DEBATE",
                agent="Coordinator",
                message=f"Round {round_num} complete. Convergence: {convergence['score']:.2f}",
                metadata={"consensus": convergence["consensus"]},
            )

            if convergence["consensus"]:
                await log_callback(
                    case_id=case_id,
                    level="SUCCESS",
                    agent="Coordinator",
                    message=f"Consensus reached after {round_num} rounds",
                )
                break

            scenarios = revised_scenarios

            if progress_callback:
                await progress_callback(
                    round_num / rounds, f"Debate round {round_num} complete"
                )

        # Select final outcome
        final_outcome = self._select_final_outcome(self.debate_history)

        return final_outcome

    def _check_convergence(self, agent_outputs: Dict) -> Dict:
        """
        Detect if agents have reached consensus.

        Consensus Criteria:
        1. All agents confidence > CONVERGENCE_THRESHOLD
        2. At least MIN_AGREEMENT_COUNT agents agree on top scenario
        3. No critical challenges remaining
        """
        confidences = []
        top_choices = []

        for agent_id, output in agent_outputs.items():
            conf = output.get("confidence", 0)
            confidences.append(conf)

            # Get top scenario choice
            scenarios = output.get("scenarios", [])
            if scenarios:
                top_choice = max(scenarios, key=lambda s: s.get("weighted_score", 0))
                top_choices.append(top_choice.get("id"))

        # Check confidence threshold
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        all_confident = all(c > self.CONVERGENCE_THRESHOLD for c in confidences)

        # Check agreement
        from collections import Counter

        choice_counts = Counter(top_choices)
        most_common = choice_counts.most_common(1)
        agreement_count = most_common[0][1] if most_common else 0

        # Veto check
        skeptic_output = agent_outputs.get("dispute_skeptic", {})
        has_veto = skeptic_output.get("consensus_veto", False)

        consensus = (
            all_confident
            and agreement_count >= self.MIN_AGREEMENT_COUNT
            and not has_veto
        )

        # Convergence score: weighted average of confidence and agreement
        agreement_ratio = agreement_count / len(agent_outputs) if agent_outputs else 0
        convergence_score = (avg_confidence * 0.6) + (agreement_ratio * 0.4)

        return {
            "consensus": consensus,
            "score": convergence_score,
            "confidence": avg_confidence,
            "agreement": agreement_ratio,
            "top_choice": most_common[0][0] if most_common else None,
        }

    def _select_final_outcome(self, debate_history: List[DebateRound]) -> Dict:
        """Select best outcome from debate history."""
        # Get final round with highest convergence
        best_round = max(debate_history, key=lambda r: r.convergence_score)

        # Extract winning scenario
        architect_output = best_round.agent_outputs.get("outcome_architect", {})
        scenarios = architect_output.get("scenarios", [])

        if not scenarios:
            return {"error": "No scenarios generated"}

        winning_scenario = max(scenarios, key=lambda s: s.get("weighted_score", 0))

        return {
            "scenario": winning_scenario,
            "debate_rounds": len(debate_history),
            "convergence_score": best_round.convergence_score,
            "consensus_reached": best_round.consensus_reached,
            "is_disputed": getattr(best_round, "disputed", False)
            or (
                best_round.round_number >= self.MAX_DEBATE_ROUNDS
                and not best_round.consensus_reached
            ),
            "agent_confidences": {
                agent: output.get("confidence", 0)
                for agent, output in best_round.agent_outputs.items()
            },
        }

    async def generate_deliverables(
        self, case_id: str, outcome: Dict, progress_callback: Callable = None
    ) -> Dict:
        """Stage 5: Generate final deliverables via Chronicle Scribe."""
        scribe = self.agents["chronicle_scribe"]

        # Strategic Report
        report = await scribe.generate_strategic_report(
            case_id=case_id, outcome=outcome
        )
        await self.memory.store_deliverable(
            case_id=case_id, deliverable_type="strategic_report", content=report
        )

        if progress_callback:
            await progress_callback(0.3, "Strategic report generated")

        # Pre-written Emails
        emails = await scribe.generate_emails(case_id=case_id, outcome=outcome)
        for email in emails:
            await self.memory.store_deliverable(
                case_id=case_id, deliverable_type="email", content=email
            )

        if progress_callback:
            await progress_callback(0.6, "Email templates generated")

        # Contact List
        contacts = await scribe.extract_contacts(case_id=case_id, outcome=outcome)

        if progress_callback:
            await progress_callback(0.8, "Contact list compiled")

        # Visual Diagrams (Mermaid)
        visuals = await scribe.generate_visuals(case_id=case_id, outcome=outcome)
        for visual in visuals:
            await self.memory.store_deliverable(
                case_id=case_id, deliverable_type="visual", content=visual
            )

        if progress_callback:
            await progress_callback(1.0, "All deliverables complete")

        # STAGE 6: Workspace Integration (Optional)
        workspace_results = None
        try:
            workspace_results = await scribe.push_to_workspace(
                case_id=case_id, report=report, emails=emails
            )
        except Exception as e:
            # Non-blocking, just log
            print(f"Workspace push skipped or failed: {e}")

        return {
            "strategic_report": report,
            "emails": emails,
            "contacts": contacts,
            "visuals": visuals,
            "outcome_summary": outcome,
            "workspace": workspace_results,
        }
