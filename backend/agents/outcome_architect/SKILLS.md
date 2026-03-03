# Outcome Architect Skills

## Scenario Generation Templates

### Legal Domain
1. Negotiation/Settlement
2. Administrative Complaint
3. Litigation (Small Claims → Superior Court)
4. Regulatory Escalation
5. Public/Media Pressure

### Insurance Domain
1. Formal Claim with Evidence
2. Appeal with New Documentation
3. State Insurance Commissioner Complaint
4. Bad Faith Litigation
5. Public Adjuster Engagement

### Employment Domain
1. Internal Resolution
2. HR Escalation
3. Regulatory Complaint (EEOC, DOL)
4. Negotiated Severance
5. Litigation

## Decision Matrix
| Criterion | Weight | Scoring |
|-----------|--------|---------|
| Impact on user | 30% | 1-10 scale |
| Probability of success | 25% | Evidence-based % |
| Time to resolution | 15% | Days, with confidence |
| Financial cost | 15% | $ estimate + variance |
| Emotional/psychological cost | 10% | 1-10 burden scale |
| Reversibility | 5% | Can we undo if wrong? |

## Output Schema
```json
{
  "scenarios": [{
    "id": "scenario_1",
    "name": "...",
    "description": "...",
    "steps": ["...", "..."],
    "scores": {"impact": 8, "probability": 0.7},
    "weighted_score": 7.4,
    "confidence": 0.82,
    "estimated_timeline": "45-60 days",
    "estimated_cost": "$2,000-3,500",
    "risks": [{"description": "...", "mitigation": "..."}],
    "best_for": "Users who prioritize speed over maximum recovery"
  }],
  "recommendation": {
    "primary": "scenario_id",
    "rationale": "...",
    "confidence": 0.85,
    "conditions": ["If X happens, switch to Y"]
  }
}
```
