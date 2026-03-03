"""
Formal debate protocol for multi-agent consensus.
Adversarial validation with structured convergence.
"""

import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np

class Stance(Enum):
    SUPPORT = "support"      # Confirm with additional evidence
    CHALLENGE = "challenge"  # Identify flaws, request evidence
    SYNTHESIZE = "synthesize" # Merge compatible viewpoints
    ABSTAIN = "abstain"      # Insufficient information

@dataclass
class Argument:
    agent_id: str
    stance: Stance
    target: Optional[str]  # Agent being responded to
    claim: str
    evidence: List[str]  # Vector memory IDs
    confidence: float
    attack_surface: List[str]  # Vulnerabilities admitted

class DebateRound:
    def __init__(self, round_number: int, topic: str, gemini_wrapper=None):
        self.round_number = round_number
        self.topic = topic
        self.arguments: List[Argument] = []
        self.consensus_map: Dict[str, float] = {}  # claim -> agreement score
        self.llm = gemini_wrapper

    def add_argument(self, arg: Argument):
        self.arguments.append(arg)

    async def calculate_consensus(self) -> Dict:
        """
        Calculate semantic consensus across arguments.
        Not just voting—measure conceptual overlap.
        """
        if len(self.arguments) < 2:
            return {"consensus": False, "score": 0.0}

        # Extract claims
        claims = [a.claim for a in self.arguments]

        # Embed claims for semantic comparison
        claim_embeddings = await self._embed_claims(claims)

        # Calculate pairwise similarity
        similarities = []
        for i in range(len(claim_embeddings)):
            for j in range(i+1, len(claim_embeddings)):
                sim = self._cosine_similarity(claim_embeddings[i], claim_embeddings[j])
                similarities.append(sim)

        avg_similarity = float(np.mean(similarities)) if similarities else 0.0
        min_confidence = min(a.confidence for a in self.arguments)

        # Consensus requires both semantic agreement AND confidence
        consensus_score = (avg_similarity * 0.6) + (min_confidence * 0.4)

        # Check for critical challenges
        challenges = [a for a in self.arguments if a.stance == Stance.CHALLENGE]
        unresolved_challenges = len([c for c in challenges if not self._is_addressed(c)])

        return {
            "consensus": consensus_score > 0.8 and unresolved_challenges == 0,
            "score": consensus_score,
            "semantic_agreement": avg_similarity,
            "confidence_floor": min_confidence,
            "unresolved_challenges": unresolved_challenges,
            "dominant_claim": self._find_dominant_claim(claim_embeddings)
        }

    async def _embed_claims(self, claims: List[str]) -> List[np.ndarray]:
        """Generate embeddings for claim comparison."""
        if not self.llm:
            # Fallback to dummy embeddings if LLM not available
            return [np.zeros(768) for _ in claims]

        # GeminiWrapper.embed expects a list[str] and supports batching.
        vectors = await self.llm.embed(claims)
        return [np.array(v) for v in vectors]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _is_addressed(self, challenge: Argument) -> bool:
        """Check if challenge has been substantively addressed."""
        challenge_idx = self.arguments.index(challenge)
        later_args = self.arguments[challenge_idx+1:]

        for arg in later_args:
            if arg.target == challenge.agent_id or any(
                c in arg.evidence for c in challenge.attack_surface
            ):
                return True
        return False

    def _find_dominant_claim(self, embeddings: List[np.ndarray]) -> str:
        """Find centroid claim that best represents consensus."""
        if not embeddings:
            return ""
        centroid = np.mean(embeddings, axis=0)
        similarities = [self._cosine_similarity(centroid, e) for e in embeddings]
        best_idx = int(np.argmax(similarities))
        return self.arguments[best_idx].claim


class DebateEngine:
    """
    Manages formal debate across multiple rounds.
    """

    def __init__(self, gemini_wrapper, max_rounds: int = 5, min_rounds: int = 2):
        self.llm = gemini_wrapper
        self.max_rounds = max_rounds
        self.min_rounds = min_rounds
        self.rounds: List[DebateRound] = []

    async def conduct_debate(
        self,
        topic: str,
        agents: List[object],
        initial_claims: List[str],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Execute full debate protocol.
        """
        current_claims = initial_claims

        for round_num in range(1, self.max_rounds + 1):
            round_obj = DebateRound(round_num, topic, self.llm)

            # Each agent responds to current state
            for agent in agents:
                # Assuming agent has formulate_argument method
                argument = await agent.formulate_argument(
                    topic=topic,
                    current_claims=current_claims,
                    previous_rounds=self.rounds,
                    available_stances=[Stance.SUPPORT, Stance.CHALLENGE, Stance.SYNTHESIZE]
                )
                round_obj.add_argument(argument)

                # Real-time broadcast
                if progress_callback:
                    await progress_callback(
                        agent_id=agent.codename,
                        stance=argument.stance.value,
                        claim_preview=argument.claim[:100]
                    )

            # Calculate round consensus
            consensus = await round_obj.calculate_consensus()
            self.rounds.append(round_obj)

            # Check termination conditions
            if round_num >= self.min_rounds and consensus["consensus"]:
                return {
                    "conclusion": consensus["dominant_claim"],
                    "rounds_conducted": round_num,
                    "consensus_score": consensus["score"],
                    "debate_transcript": self._compile_transcript()
                }

            # Prepare next round
            if consensus["dominant_claim"]:
                current_claims = [consensus["dominant_claim"]]

        # Max rounds reached without consensus
        return {
            "conclusion": self._force_convergence(),
            "rounds_conducted": self.max_rounds,
            "consensus_score": consensus["score"] if 'consensus' in locals() else 0.0,
            "debate_transcript": self._compile_transcript(),
            "note": "Forced convergence—review minority reports"
        }

    def _compile_transcript(self) -> List[Dict]:
        """Compile full debate record for transparency."""
        transcript = []
        for round in self.rounds:
            for arg in round.arguments:
                transcript.append({
                    "round": round.round_number,
                    "agent": arg.agent_id,
                    "stance": arg.stance.value,
                    "claim": arg.claim,
                    "confidence": arg.confidence,
                    "evidence_count": len(arg.evidence)
                })
        return transcript

    def _force_convergence(self) -> str:
        """Select best claim when debate doesn't naturally converge."""
        all_args = []
        for round in self.rounds:
            for arg in round.arguments:
                recency_boost = 1 + (round.round_number * 0.1)
                all_args.append((arg, arg.confidence * recency_boost))

        all_args.sort(key=lambda x: x[1], reverse=True)
        return all_args[0][0].claim if all_args else "No conclusion reached"
