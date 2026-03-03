"""
Test suite for swarm debate and consensus.
"""

import pytest
import asyncio
from typing import List, Dict, Optional, Any
from enum import Enum

class Stance(Enum):
    SUPPORT = "support"
    CHALLENGE = "challenge"
    NEUTRAL = "neutral"

class Argument:
    def __init__(self, agent_id: str, stance: Stance, target: Optional[str],
                 claim: str, evidence: List[str], confidence: float, attack_surface: List[str]):
        self.agent_id = agent_id
        self.stance = stance
        self.target = target
        self.claim = claim
        self.evidence = evidence
        self.confidence = confidence
        self.attack_surface = attack_surface

class DebateOrchestrator:
    """Mock orchestrator for testing consensus logic."""
    def __init__(self, max_rounds: int = 3, min_rounds: int = 2):
        self.max_rounds = max_rounds
        self.min_rounds = min_rounds

    async def conduct_debate(self, topic: str, agents: List[Any], initial_claims: List[str]) -> Dict:
        rounds = 0
        consensus_reached = False
        last_claims = []

        for r in range(self.max_rounds):
            rounds += 1
            current_round_arguments = []
            for agent in agents:
                arg = await agent.formulate_argument(topic, initial_claims, r, [Stance.SUPPORT, Stance.CHALLENGE])
                current_round_arguments.append(arg)

            # Simplified consensus check: if all active claims match
            claims = [a.claim for a in current_round_arguments]
            if len(set(claims)) == 1 and rounds >= self.min_rounds:
                consensus_reached = True
                break

        result = {
            "conclusion": claims[0] if consensus_reached or rounds == self.max_rounds else "no_consensus",
            "rounds_conducted": rounds,
            "consensus_score": 0.9 if consensus_reached else 0.4
        }
        if rounds == self.max_rounds and not consensus_reached:
            result["note"] = "Forced convergence: Max rounds reached without perfect consensus"

        return result

@pytest.mark.asyncio
async def test_simple_consensus():
    """Test that agents reach consensus on straightforward case."""
    orchestrator = DebateOrchestrator(max_rounds=3, min_rounds=2)

    # Mock agents
    class MockAgent:
        def __init__(self, agent_id, preferred_outcome):
            self.agent_id = agent_id
            self.preferred = preferred_outcome

        async def formulate_argument(self, topic, current_claims, round_num, available_stances):
            # All agree on same outcome
            return Argument(
                agent_id=self.agent_id,
                stance=Stance.SUPPORT,
                target=None,
                claim=self.preferred,
                evidence=["doc_1", "doc_2"],
                confidence=0.85,
                attack_surface=[]
            )

    agents = [
        MockAgent("agent_1", "settlement"),
        MockAgent("agent_2", "settlement"),
        MockAgent("agent_3", "settlement")
    ]

    result = await orchestrator.conduct_debate(
        topic="insurance dispute resolution",
        agents=agents,
        initial_claims=["litigation", "settlement", "mediation"]
    )

    assert result["conclusion"] == "settlement"
    assert result["rounds_conducted"] == 2  # Min rounds, early convergence
    assert result["consensus_score"] > 0.8

@pytest.mark.asyncio
async def test_divergent_scenarios_require_max_rounds():
    """Test that disagreement forces max rounds."""
    orchestrator = DebateOrchestrator(max_rounds=5, min_rounds=2)

    class DisagreeingAgent:
        def __init__(self, agent_id, preferred):
            self.agent_id = agent_id
            self.preferred = preferred

        async def formulate_argument(self, topic, current_claims, round_num, available_stances):
            # Challenge others or support their own view
            # Agent 1 will keep pushing its own view even if others differ
            return Argument(
                agent_id=self.agent_id,
                stance=Stance.CHALLENGE if round_num > 0 else Stance.SUPPORT,
                target="agent_2" if self.agent_id == "agent_1" else None,
                claim=self.preferred,
                evidence=["evidence_for_my_view"],
                confidence=0.75,
                attack_surface=["cost_uncertainty"]
            )

    agents = [
        DisagreeingAgent("agent_1", "litigation"),
        DisagreeingAgent("agent_2", "settlement"),
        DisagreeingAgent("agent_3", "mediation")
    ]

    result = await orchestrator.conduct_debate(
        topic="complex dispute",
        agents=agents,
        initial_claims=["litigation", "settlement", "mediation"]
    )

    assert result["rounds_conducted"] == 5  # Max rounds
    assert "note" in result  # Forced convergence warning
    assert result["consensus_score"] < 0.8
