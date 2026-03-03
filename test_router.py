#!/usr/bin/env python3
import sys

sys.path.insert(0, ".")
print("1: importing pathlib")
from pathlib import Path

print("2: importing router")
from backend.ingestion.router import FileIngestionRouter

print("3: creating router")
r = FileIngestionRouter()
print("4: calling chunk_text")
sys.stdout.flush()
result = r._chunk_text("test content here " * 10, "test.txt")
print("5: got result")
sys.stdout.flush()
print(f"Chunks: {len(result)}")
print("Done")
