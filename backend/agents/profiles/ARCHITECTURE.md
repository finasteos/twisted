# TWISTED Agent Architecture

## The Memory System

As an agent in TWISTED, you are part of a structured agent swarm. Here's how memory and information flow works:

### Folder Structure

```
backend/agents/profiles/{agent_name}/
├── IDENTITY.md    # Who am I? (name, role, personality)
├── SKILLS.md      # What can I do? (capabilities, tools)
├── SOUL.md        # How do I think? (patterns, style)
├── config.json    # Settings (model, temperature)
└── SystemAgent.md # My system prompt (loaded at runtime)
```

### Memory Types

1. **Core Identity** (Files above)
   - Loaded at agent initialization
   - Defines who you are and what you do
   - Edits persist across runs

2. **Vector Memory** (Qdrant)
   - Semantic search across past cases
   - Retrieved when relevant to current query
   - Not human-readable directly

3. **Session Memory** (workspace/)
   - Current case evidence and research
   - Temporary during case processing
   - Archived after completion

### How to Use Memory

- **Read**: Check IDENTITY.md, SKILLS.md of other agents to understand team capabilities
- **Write**: Your findings can be stored to Qdrant for future retrieval
- **Search**: Query vector memory for similar past cases
- **Learn**: Update SOUL.md with patterns you notice

### Agent Relationships

You are part of a swarm. Typical flow:

```
User Query → Coordinator → Context Weaver (extract)
                              ↓
                        Echo Vault (research)
                              ↓
                        Outcome Architect (strategy)
                              ↓
                        Chronicle Scribe (output)
```

### Your Role

1. Read your IDENTITY.md to know who you are
2. Check SKILLS.md to know what tools you have access to
3. Review SOUL.md for your thinking patterns
4. Process your task and report back to Coordinator
5. Store useful information to memory for future runs

---

*This architecture allows agents to be added/removed dynamically. Each agent is self-contained in its folder.*
