# Context Weaver Skills

## Multi-Modal Extraction
- Text: Named Entity Recognition (NER) via Gemini 3 Flash
- Images: OCR + object detection + scene context
- Video: Keyframe analysis + transcript extraction + scene detection
- Audio: Whisper MLX transcription + speaker diarization

## Vector Query Patterns
"Who are the main individuals involved?"
"What are the key dates and deadlines?"
"What financial amounts are mentioned?"
"What legal or regulatory references exist?"
"What health or safety concerns appear?"

## Output Schema
```json
{
  "entities": {
    "people": [{"name": "...", "role": "...", "contact_hints": []}],
    "organizations": [{"name": "...", "type": "...", "jurisdiction": "..."}],
    "dates": [{"date": "ISO8601", "significance": "...", "deadline_type": "soft|hard"}],
    "financials": [{"amount": 0.0, "currency": "...", "context": "..."}]
  },
  "relationships": [{"source": "...", "target": "...", "type": "...", "evidence": "..."}],
  "timeline": [{"date": "...", "event": "...", "significance": "...", "sources": []}],
  "risk_flags": [{"severity": 1-10, "category": "...", "description": "...", "urgency": "..."}]
}
```
