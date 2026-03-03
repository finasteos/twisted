# Coordinator Skills

## Task Management
- Priority queue implementation with dynamic reordering
- Resource allocation based on case complexity score
- Worker pool management (max 8 concurrent agents)
- Deadlock detection and resolution

## State Machine
IDLE → INGESTING → ANALYZING → DEBATING → SYNTHESIZING → DELIVERING → COMPLETE

## Convergence Detection
```python
def check_convergence(agent_outputs: List[Dict]) -> bool:
    confidences = [a["confidence"] for a in agent_outputs]
    stances = [a["recommended_action"] for a in agent_outputs]

    # High confidence agreement
    if all(c > 0.8 for c in confidences) and len(set(stances)) == 1:
        return True

    # Semantic similarity of recommendations
    # (uses vector similarity via ChromaDB)
    return semantic_convergence(stances) > 0.85

Error Recovery
Retry: Up to 3 attempts with exponential backoff
Escalate: To human if confidence <0.5 after 3 rounds
Degrade: Reduce model tier if rate limited
