"""
Complete audit trail for all system actions.
Immutable, tamper-evident logging.
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class AuditTrail:
    """
    Blockchain-inspired audit chain.
    Each entry hashes previous entry for tamper evidence.
    """

    def __init__(self, case_id: str, storage_path: str = "./audit_logs"):
        self.case_id = case_id
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.chain_file = self.storage_path / f"{case_id}.chain"
        self.previous_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        """Load hash of last entry for chain continuity."""
        if not self.chain_file.exists():
            return "0" * 64  # Genesis

        with open(self.chain_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64

            last_entry = json.loads(lines[-1])
            return last_entry["hash"]

    def log(self, action: str, actor: str, details: Dict,
            sensitivity: str = "normal") -> Dict:
        """
        Append immutable audit entry.
        """
        timestamp = time.time()

        entry = {
            "timestamp": timestamp,
            "datetime": datetime.utcfromtimestamp(timestamp).isoformat(),
            "case_id": self.case_id,
            "action": action,
            "actor": actor,  # agent_id, user_id, or "system"
            "details": details,
            "sensitivity": sensitivity,
            "previous_hash": self.previous_hash
        }

        # Calculate hash
        entry_json = json.dumps(entry, sort_keys=True)
        entry["hash"] = hashlib.sha256(entry_json.encode()).hexdigest()

        # Append to chain
        with open(self.chain_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        self.previous_hash = entry["hash"]

        return entry

    def verify_chain(self) -> Dict:
        """
        Verify integrity of audit chain.
        Detects tampering.
        """
        if not self.chain_file.exists():
            return {"valid": True, "entries": 0}

        with open(self.chain_file, 'r') as f:
            entries = [json.loads(line) for line in f]

        for i, entry in enumerate(entries):
            # Verify hash chain
            if i == 0:
                expected_previous = "0" * 64
            else:
                expected_previous = entries[i-1]["hash"]

            if entry["previous_hash"] != expected_previous:
                return {
                    "valid": False,
                    "tampered_at_entry": i,
                    "expected_previous": expected_previous,
                    "actual_previous": entry["previous_hash"]
                }

            # Verify entry hash
            entry_copy = {k: v for k, v in entry.items() if k != "hash"}
            calculated_hash = hashlib.sha256(
                json.dumps(entry_copy, sort_keys=True).encode()
            ).hexdigest()

            if calculated_hash != entry["hash"]:
                return {
                    "valid": False,
                    "tampered_at_entry": i,
                    "hash_mismatch": True
                }

        return {
            "valid": True,
            "entries": len(entries),
            "chain_hash": entries[-1]["hash"] if entries else "0" * 64
        }

    def get_entries(self, since: Optional[float] = None,
                   actor: Optional[str] = None) -> List[Dict]:
        """Query audit trail."""
        entries = []

        if not self.chain_file.exists():
            return []

        with open(self.chain_file, 'r') as f:
            for line in f:
                entry = json.loads(line)

                if since and entry["timestamp"] < since:
                    continue
                if actor and entry["actor"] != actor:
                    continue

                entries.append(entry)

        return entries
