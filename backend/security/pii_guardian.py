"""
PII detection and redaction.
Prevents accidental exposure in logs and vectors.
"""

import re
from typing import List, Dict, Tuple

class PIIGuardian:
    """
    Scans content for personally identifiable information.
    Redacts or flags for encryption.
    """

    PII_PATTERNS = {
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "bank_account": r'\b\d{8,17}\b',
        "passport": r'\b[A-Z]{2}\d{7}\b',
    }

    def scan(self, text: str) -> Dict:
        """
        Scan text for PII. Return locations and types.
        """
        findings = []

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = list(re.finditer(pattern, text))
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),  # In production, don't store raw
                    "confidence": "high" if len(match.group()) > 8 else "medium"
                })

        return {
            "pii_detected": len(findings) > 0,
            "findings": findings,
            "risk_level": self._calculate_risk(findings),
            "redacted_preview": self._redact_preview(text, findings)
        }

    def redact(self, text: str, findings: List[Dict]) -> str:
        """
        Replace PII with [REDACTED-type] placeholders.
        """
        # Sort by position, reverse to avoid offset issues
        sorted_findings = sorted(findings, key=lambda x: x["start"], reverse=True)

        result = text
        for finding in sorted_findings:
            placeholder = f"[REDACTED-{finding['type'].upper()}]"
            result = result[:finding["start"]] + placeholder + result[finding["end"]:]

        return result

    def _calculate_risk(self, findings: List[Dict]) -> str:
        """Calculate overall PII risk level."""
        high_confidence = sum(1 for f in findings if f["confidence"] == "high")

        if high_confidence > 5:
            return "critical"
        elif high_confidence > 2 or len(findings) > 5:
            return "high"
        elif len(findings) > 0:
            return "medium"
        return "low"

    def _redact_preview(self, text: str, findings: List[Dict]) -> str:
        """Create safe preview for logging."""
        if not text:
            return ""
        preview_text = text[:200]
        if len(text) > 200:
            preview_text += "..."
        return self.redact(preview_text, findings)
