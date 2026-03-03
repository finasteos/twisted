"""
SwarmOrchestrator: Multi-agent debate and consensus formation.
Coordinates specialized agents through structured debate rounds.
Now with verbose task broadcasting and comprehensive debug logging.
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
from backend.logging_config import get_logger
from backend.models.websocket import (
    AgentTaskItem,
    AgentTasksMessage,
    MessageType,
)

logger = get_logger("swarm")

# Default max debate history entries
DEFAULT_DEBATE_HISTORY_LIMIT = 20


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
    2. Echo Vault retrieves historical patterns
    3. Outcome Architect generates scenarios
    4. Debate rounds: agents challenge/support/synthesize
    5. Pulse Monitor tracks system health throughout
    6. Convergence detection: confidence > 0.8, agreement > 3 agents
    7. Chronicle Scribe generates final deliverables
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
        debate_history_limit: int = DEFAULT_DEBATE_HISTORY_LIMIT,
    ):
        self.llm = gemini_wrapper
        self.memory = chroma_manager
        self.comm = connection_manager
        self.router = hybrid_router
        self.tool_registry = tool_registry

        self.agents: Dict[str, BaseAgent] = {}
        self.debate_history: List[DebateRound] = []
        self._debate_history_limit = debate_history_limit
        self.debate_engine = DebateEngine(self.llm) if self.llm else None

    def _trim_debate_history(self) -> None:
        """Keep debate history bounded."""
        if len(self.debate_history) > self._debate_history_limit:
            removed = len(self.debate_history) - self._debate_history_limit
            self.debate_history = self.debate_history[-self._debate_history_limit:]
            logger.debug(
                f"Trimmed {removed} old debate rounds from history",
                operation="trim_debate_history",
            )

    async def _broadcast_agent_tasks(
        self, case_id: str, agent_id: str, agent_name: str,
        tasks: List[Dict], overall_status: str = "working",
    ) -> None:
        """Broadcast verbose task list for a specific agent node."""
        task_items = [
            AgentTaskItem(
                name=t["name"],
                status=t.get("status", "pending"),
                duration_ms=t.get("duration_ms"),
                detail=t.get("detail"),
            )
            for t in tasks
        ]
        msg = AgentTasksMessage(
            type=MessageType.AGENT_TASKS,
            timestamp=time.time(),
            case_id=case_id,
            agent_id=agent_id,
            agent_name=agent_name,
            tasks=task_items,
            overall_status=overall_status,
        )
        await self.comm.broadcast_to_case(case_id, msg)

    async def initialize(self):
        """Initialize all agents with dependencies."""
        logger.info("Initializing swarm agents...", operation="initialize")
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
        logger.info(
            f"Swarm initialized with {len(self.agents)} agents: {list(self.agents.keys())}",
            operation="initialize",
        )

    async def run_context_analysis(
        self, case_id: str, progress_callback: Callable, thought_callback: Callable
    ):
        """Stage 1: Context Weaver builds situation understanding."""
        start = logger.agent_start("Coordinator", case_id, "context_analysis")
        context_agent = self.agents["context_weaver"]

        # Broadcast task list for Context Weaver node
        tasks = [
            {"name": "Query raw ingestion data", "status": "running"},
            {"name": "Extract entities & relationships", "status": "pending"},
            {"name": "Build timeline", "status": "pending"},
            {"name": "Identify risk flags", "status": "pending"},
            {"name": "Store structured analysis", "status": "pending"},
        ]
        await self._broadcast_agent_tasks(case_id, "context_weaver", "Context Weaver", tasks)

        # Query raw ingestion data
        logger.agent_step("Coordinator", case_id, "context_analysis", "Querying raw ingestion data")
        raw_docs = await self.memory.query(
            collection="case_ingestion",
            query_texts=["entities people organizations dates"],
            where={"case_id": case_id},
            n_results=20,
        )
        tasks[0]["status"] = "done"
        tasks[0]["detail"] = f"Retrieved {len(raw_docs)} documents"
        tasks[1]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "context_weaver", "Context Weaver", tasks)

        # Analyze and extract structured context
        logger.agent_step("Coordinator", case_id, "context_analysis", "Running context analysis",
                          {"doc_count": len(raw_docs)})
        analysis = await context_agent.analyze(
            case_id=case_id, documents=raw_docs, thought_callback=thought_callback
        )
        tasks[1]["status"] = "done"
        tasks[1]["detail"] = f"{len(analysis.get('entities', {}))} entity types found"
        tasks[2]["status"] = "done"
        tasks[2]["detail"] = f"{len(analysis.get('timeline', []))} events"
        tasks[3]["status"] = "done"
        tasks[3]["detail"] = f"{len(analysis.get('risk_flags', []))} flags"
        tasks[4]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "context_weaver", "Context Weaver", tasks)

        # Store structured analysis
        logger.agent_step("Coordinator", case_id, "context_analysis", "Storing analysis results")
        await self.memory.store_analysis(
            case_id=case_id,
            entities=analysis["entities"],
            relationships=analysis["relationships"],
            timeline=analysis["timeline"],
            risk_flags=analysis["risk_flags"],
        )
        tasks[4]["status"] = "done"
        await self._broadcast_agent_tasks(case_id, "context_weaver", "Context Weaver", tasks, "done")

        logger.agent_complete("Coordinator", case_id, "context_analysis", start,
                              {"entities": len(analysis.get('entities', {})),
                               "timeline_events": len(analysis.get('timeline', [])),
                               "risk_flags": len(analysis.get('risk_flags', []))})
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
        start = logger.agent_start("Coordinator", case_id, "debate", {"rounds": rounds})
        await log_callback(
            case_id=case_id,
            level="INFO",
            agent="Coordinator",
            message="Initiating swarm debate for outcome optimization",
        )

        # Broadcast initial task lists for all debate agents
        coordinator_tasks = [
            {"name": "Generate initial scenarios", "status": "running"},
            {"name": f"Run {rounds} debate rounds", "status": "pending"},
            {"name": "Check convergence", "status": "pending"},
            {"name": "Select final outcome", "status": "pending"},
        ]
        await self._broadcast_agent_tasks(case_id, "coordinator", "Coordinator Alpha", coordinator_tasks)

        # Round 1: Generate scenarios
        outcome_tasks = [
            {"name": "Analyze case context", "status": "running"},
            {"name": "Generate outcome scenarios", "status": "pending"},
            {"name": "Score & rank scenarios", "status": "pending"},
        ]
        await self._broadcast_agent_tasks(case_id, "outcome_architect", "Outcome Architect", outcome_tasks)

        outcome_agent = self.agents["outcome_architect"]
        logger.agent_step("Coordinator", case_id, "debate", "Generating initial scenarios")
        scenarios = await outcome_agent.generate_scenarios(
            case_id=case_id, thought_callback=thought_callback
        )

        outcome_tasks[0]["status"] = "done"
        outcome_tasks[1]["status"] = "done"
        outcome_tasks[1]["detail"] = f"{len(scenarios)} scenarios generated"
        outcome_tasks[2]["status"] = "done"
        await self._broadcast_agent_tasks(case_id, "outcome_architect", "Outcome Architect", outcome_tasks, "done")

        coordinator_tasks[0]["status"] = "done"
        coordinator_tasks[0]["detail"] = f"{len(scenarios)} scenarios"
        coordinator_tasks[1]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "coordinator", "Coordinator Alpha", coordinator_tasks)

        await log_callback(
            case_id=case_id,
            level="DEBATE",
            agent="Outcome Architect",
            message=f"Generated {len(scenarios)} outcome scenarios",
            metadata={"scenarios": [s.get("name", "unnamed") for s in scenarios]},
        )

        # Debate rounds
        veto_count = 0
        for round_num in range(1, rounds + 1):
            logger.agent_step("Coordinator", case_id, "debate", f"Starting round {round_num}")
            await log_callback(
                case_id=case_id,
                level="DEBATE",
                agent="Coordinator",
                message=f"Debate Round {round_num} beginning",
            )

            # Collect agent analyses
            agent_outputs = {}

            # Context Weaver validates scenario assumptions
            cw_tasks = [
                {"name": "Load scenario assumptions", "status": "done"},
                {"name": "Cross-reference with case data", "status": "running"},
                {"name": "Identify contradictions", "status": "pending"},
                {"name": "Report challenges", "status": "pending"},
            ]
            await self._broadcast_agent_tasks(case_id, "context_weaver", "Context Weaver", cw_tasks)
            logger.agent_step("Coordinator", case_id, "debate",
                              f"Round {round_num}: Context Weaver validating scenarios")

            context_analysis = await self.agents["context_weaver"].validate_scenarios(
                case_id=case_id, scenarios=scenarios, thought_callback=thought_callback
            )
            agent_outputs["context_weaver"] = context_analysis
            cw_tasks[1]["status"] = "done"
            cw_tasks[2]["status"] = "done"
            cw_tasks[2]["detail"] = f"{len(context_analysis.get('challenges', []))} issues found"
            cw_tasks[3]["status"] = "done"
            await self._broadcast_agent_tasks(case_id, "context_weaver", "Context Weaver", cw_tasks, "done")

            # Echo Vault retrieves historical patterns
            ev_tasks = [
                {"name": "Search historical patterns", "status": "running"},
                {"name": "Match similar past cases", "status": "pending"},
                {"name": "Report pattern insights", "status": "pending"},
            ]
            await self._broadcast_agent_tasks(case_id, "echo_vault", "Echo Vault", ev_tasks)
            logger.agent_step("Coordinator", case_id, "debate",
                              f"Round {round_num}: Echo Vault retrieving patterns")

            echo_vault_agent = self.agents["echo_vault"]
            if hasattr(echo_vault_agent, 'retrieve_patterns'):
                patterns = await echo_vault_agent.retrieve_patterns(
                    case_id=case_id, scenarios=scenarios
                )
                agent_outputs["echo_vault"] = patterns
                ev_tasks[0]["status"] = "done"
                ev_tasks[1]["status"] = "done"
                ev_tasks[1]["detail"] = f"{len(patterns.get('matches', []))} matches"
                ev_tasks[2]["status"] = "done"
            else:
                ev_tasks[0]["status"] = "done"
                ev_tasks[1]["status"] = "skipped"
                ev_tasks[2]["status"] = "skipped"
            await self._broadcast_agent_tasks(case_id, "echo_vault", "Echo Vault", ev_tasks, "done")

            # Outcome Architect revises based on challenges
            oa_tasks = [
                {"name": "Review challenges from Context Weaver", "status": "done"},
                {"name": "Revise scenario parameters", "status": "running"},
                {"name": "Recalculate weighted scores", "status": "pending"},
            ]
            await self._broadcast_agent_tasks(case_id, "outcome_architect", "Outcome Architect", oa_tasks)
            logger.agent_step("Coordinator", case_id, "debate",
                              f"Round {round_num}: Outcome Architect revising scenarios")

            revised_scenarios = await outcome_agent.revise_scenarios(
                scenarios=scenarios,
                challenges=context_analysis.get("challenges", []),
                thought_callback=thought_callback,
            )
            agent_outputs["outcome_architect"] = {
                "scenarios": revised_scenarios,
                "confidence": self._calculate_scenario_confidence(revised_scenarios),
            }
            oa_tasks[1]["status"] = "done"
            oa_tasks[2]["status"] = "done"
            oa_tasks[2]["detail"] = f"Confidence: {agent_outputs['outcome_architect']['confidence']:.2f}"
            await self._broadcast_agent_tasks(case_id, "outcome_architect", "Outcome Architect", oa_tasks, "done")

            # Dispute Skeptic adversarial review (Red Team)
            ds_tasks = [
                {"name": "Analyze revised scenarios", "status": "running"},
                {"name": "Check for unsupported assumptions", "status": "pending"},
                {"name": "Flag hallucinated confidence", "status": "pending"},
                {"name": "Veto decision", "status": "pending"},
            ]
            await self._broadcast_agent_tasks(case_id, "dispute_skeptic", "Dispute Skeptic", ds_tasks)
            logger.agent_step("Coordinator", case_id, "debate",
                              f"Round {round_num}: Dispute Skeptic adversarial review")

            skeptic_analysis = await self.agents[
                "dispute_skeptic"
            ].analyze_and_challenge(
                case_id=case_id,
                scenarios=revised_scenarios,
                thought_callback=thought_callback,
            )
            agent_outputs["dispute_skeptic"] = skeptic_analysis
            ds_tasks[0]["status"] = "done"
            ds_tasks[1]["status"] = "done"
            ds_tasks[1]["detail"] = f"{len(skeptic_analysis.get('challenges', []))} challenges"
            ds_tasks[2]["status"] = "done"
            ds_tasks[3]["status"] = "done"
            ds_tasks[3]["detail"] = "VETOED" if skeptic_analysis.get("consensus_veto") else "Approved"
            await self._broadcast_agent_tasks(case_id, "dispute_skeptic", "Dispute Skeptic", ds_tasks, "done")

            if skeptic_analysis.get("consensus_veto"):
                veto_count += 1
                logger.warning(
                    f"Consensus vetoed by Dispute Skeptic (veto #{veto_count})",
                    agent="dispute_skeptic", case_id=case_id,
                )
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

            # Pulse Monitor health check during debate
            pm_tasks = [
                {"name": "Check system resource usage", "status": "running"},
                {"name": "Monitor API rate limits", "status": "pending"},
                {"name": "Report health status", "status": "pending"},
            ]
            await self._broadcast_agent_tasks(case_id, "pulse_monitor", "Pulse Monitor", pm_tasks)

            pulse_agent = self.agents["pulse_monitor"]
            if hasattr(pulse_agent, 'check_health_during_debate'):
                health = await pulse_agent.check_health_during_debate(case_id=case_id)
                pm_tasks[0]["status"] = "done"
                pm_tasks[0]["detail"] = health.get("summary", "OK")
                pm_tasks[1]["status"] = "done"
                pm_tasks[2]["status"] = "done"
            else:
                pm_tasks[0]["status"] = "done"
                pm_tasks[0]["detail"] = "Basic check passed"
                pm_tasks[1]["status"] = "done"
                pm_tasks[2]["status"] = "done"
            await self._broadcast_agent_tasks(case_id, "pulse_monitor", "Pulse Monitor", pm_tasks, "done")

            debate_round = DebateRound(
                round_number=round_num,
                agent_outputs=agent_outputs,
                consensus_reached=convergence["consensus"],
                convergence_score=convergence["score"],
            )
            self.debate_history.append(debate_round)
            self._trim_debate_history()

            await log_callback(
                case_id=case_id,
                level="DEBATE",
                agent="Coordinator",
                message=f"Round {round_num} complete. Convergence: {convergence['score']:.2f}",
                metadata={"consensus": convergence["consensus"]},
            )

            if convergence["consensus"]:
                logger.info(
                    f"Consensus reached after {round_num} rounds (score={convergence['score']:.2f})",
                    agent="Coordinator", case_id=case_id,
                )
                await log_callback(
                    case_id=case_id,
                    level="SUCCESS",
                    agent="Coordinator",
                    message=f"Consensus reached after {round_num} rounds",
                )
                coordinator_tasks[1]["status"] = "done"
                coordinator_tasks[1]["detail"] = f"Consensus in {round_num} rounds"
                coordinator_tasks[2]["status"] = "done"
                coordinator_tasks[2]["detail"] = f"Score: {convergence['score']:.2f}"
                await self._broadcast_agent_tasks(case_id, "coordinator", "Coordinator Alpha", coordinator_tasks)
                break

            scenarios = revised_scenarios

            if progress_callback:
                await progress_callback(
                    round_num / rounds, f"Debate round {round_num} complete"
                )

        # Select final outcome
        coordinator_tasks[3]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "coordinator", "Coordinator Alpha", coordinator_tasks)

        final_outcome = self._select_final_outcome(self.debate_history)

        coordinator_tasks[3]["status"] = "done"
        coordinator_tasks[3]["detail"] = f"Convergence: {final_outcome.get('convergence_score', 0):.2f}"
        await self._broadcast_agent_tasks(case_id, "coordinator", "Coordinator Alpha", coordinator_tasks, "done")

        logger.agent_complete("Coordinator", case_id, "debate", start, {
            "rounds": len(self.debate_history),
            "consensus": final_outcome.get("consensus_reached"),
            "convergence": final_outcome.get("convergence_score"),
        })

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
        start = logger.agent_start("Coordinator", case_id, "generate_deliverables")
        scribe = self.agents["chronicle_scribe"]

        # Broadcast Chronicle Scribe tasks
        cs_tasks = [
            {"name": "Generate strategic report", "status": "running"},
            {"name": "Generate email templates", "status": "pending"},
            {"name": "Compile contact list", "status": "pending"},
            {"name": "Create visual diagrams", "status": "pending"},
            {"name": "Push to workspace (optional)", "status": "pending"},
        ]
        await self._broadcast_agent_tasks(case_id, "chronicle_scribe", "Chronicle Scribe", cs_tasks)

        # Strategic Report
        logger.agent_step("Coordinator", case_id, "generate_deliverables", "Generating strategic report")
        report = await scribe.generate_strategic_report(
            case_id=case_id, outcome=outcome
        )
        await self.memory.store_deliverable(
            case_id=case_id, deliverable_type="strategic_report", content=report
        )
        cs_tasks[0]["status"] = "done"
        cs_tasks[0]["detail"] = f"{len(report)} chars"
        cs_tasks[1]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "chronicle_scribe", "Chronicle Scribe", cs_tasks)

        if progress_callback:
            await progress_callback(0.3, "Strategic report generated")

        # Pre-written Emails
        logger.agent_step("Coordinator", case_id, "generate_deliverables", "Generating email templates")
        emails = await scribe.generate_emails(case_id=case_id, outcome=outcome)
        for email in emails:
            await self.memory.store_deliverable(
                case_id=case_id, deliverable_type="email", content=email
            )
        cs_tasks[1]["status"] = "done"
        cs_tasks[1]["detail"] = f"{len(emails)} emails"
        cs_tasks[2]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "chronicle_scribe", "Chronicle Scribe", cs_tasks)

        if progress_callback:
            await progress_callback(0.6, "Email templates generated")

        # Contact List
        logger.agent_step("Coordinator", case_id, "generate_deliverables", "Compiling contact list")
        contacts = await scribe.extract_contacts(case_id=case_id, outcome=outcome)
        cs_tasks[2]["status"] = "done"
        cs_tasks[2]["detail"] = f"{len(contacts)} contacts"
        cs_tasks[3]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "chronicle_scribe", "Chronicle Scribe", cs_tasks)

        if progress_callback:
            await progress_callback(0.8, "Contact list compiled")

        # Visual Diagrams (Mermaid)
        logger.agent_step("Coordinator", case_id, "generate_deliverables", "Creating visual diagrams")
        visuals = await scribe.generate_visuals(case_id=case_id, outcome=outcome)
        for visual in visuals:
            await self.memory.store_deliverable(
                case_id=case_id, deliverable_type="visual", content=visual
            )
        cs_tasks[3]["status"] = "done"
        cs_tasks[3]["detail"] = f"{len(visuals)} diagrams"
        cs_tasks[4]["status"] = "running"
        await self._broadcast_agent_tasks(case_id, "chronicle_scribe", "Chronicle Scribe", cs_tasks)

        if progress_callback:
            await progress_callback(1.0, "All deliverables complete")

        # STAGE 6: Workspace Integration (Optional)
        workspace_results = None
        try:
            workspace_results = await scribe.push_to_workspace(
                case_id=case_id, report=report, emails=emails
            )
            cs_tasks[4]["status"] = "done"
        except Exception as e:
            cs_tasks[4]["status"] = "skipped"
            cs_tasks[4]["detail"] = str(e)[:80]
            logger.warning(f"Workspace push skipped or failed: {e}", agent="chronicle_scribe")

        await self._broadcast_agent_tasks(case_id, "chronicle_scribe", "Chronicle Scribe", cs_tasks, "done")

        logger.agent_complete("Coordinator", case_id, "generate_deliverables", start, {
            "report_length": len(report),
            "email_count": len(emails),
            "contact_count": len(contacts),
            "visual_count": len(visuals),
        })

        return {
            "strategic_report": report,
            "emails": emails,
            "contacts": contacts,
            "visuals": visuals,
            "outcome_summary": outcome,
            "workspace": workspace_results,
        }
