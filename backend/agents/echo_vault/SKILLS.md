# Echo Vault Skills

## Embedding Strategy
- Text: Gemini 3 Flash text-embedding-004 (768-dim)
- Images: CLIP-style multimodal embeddings
- Structured: JSON-aware embedding with field weighting

## ChromaDB Collections
| Collection | Purpose | Embedding Model |
|------------|---------|-----------------|
| case_ingestion | Raw extracted content | text-embedding-004 |
| case_analysis | Processed entities/relationships | text-embedding-004 |
| external_intel | Deep Research + web search | text-embedding-004 |
| swarm_deliberation | Agent debate logs | text-embedding-004 |
| final_deliverables | Generated outputs | text-embedding-004 |

## Retrieval Optimization
- Query expansion: 3 semantic variants per agent query
- Reranking: Cross-encoder for final result ordering
- Caching: LRU cache for frequent queries (1-hour TTL)
- Hybrid search: Vector + BM25 for keyword-heavy queries

## Compression
- Product quantization: 768-dim → 96-dim for storage
- Lossy but retrievable: <3% recall degradation
