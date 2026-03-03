#!/usr/bin/env python3
import sys

sys.path.insert(0, ".")

# Just do the chunk function manually
text = "test content here " * 10
source = "test.txt"
chunk_size = 1000

chunks = []
start = 0
text_length = len(text)

print(f"text_length: {text_length}")
print(f"Starting loop...")

while start < text_length:
    print(f"  start: {start}, text_length: {text_length}")
    end = min(start + chunk_size, text_length)
    chunk_text = text[start:end]
    chunks.append({"text": chunk_text})
    start = end - 100

print(f"Created {len(chunks)} chunks")
