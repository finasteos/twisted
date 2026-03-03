# Decision Engine

A local-first, automated decision-engine application that processes files to generate strategic recommendations for specific beneficiaries.

## Features

- **Drag & Drop Interface**: Drop files/folders for analysis
- **Multi-Agent AI System**: Context Analyzer, Legal Advisor, Strategist, Final Reviewer
- **Local LLM Support**: LMStudio, Google Gemini, OpenAI, Apple MLX
- **Vector Memory**: ChromaDB semantic search
- **Comprehensive Parsing**: Text, PDF, DOCX, Email, Images, Video/Audio

## Quick Start

### 1. Setup Python Environment

```bash
# Clone and setup
cd DecisionEngine
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure LLM (Optional)

**Option A: LMStudio (Recommended for Local)**
1. Download LMStudio from https://lmstudio.ai
2. Start LMStudio and download a model (e.g., Llama 3)
3. Start the server (click "Start Server" in LMStudio)
4. Backend auto-detects at localhost:1234

**Option B: Google Gemini**
1. Get API key: https://aistudio.google.com/apikey
2. Add to `.env`: `GEMINI_API_KEY=your_key_here`

### 3. Run Backend

```bash
source .venv/bin/activate
python backend/main.py
```

Backend runs at http://localhost:8000

### 4. Run SwiftUI App

Open `DecisionEngine/` in Xcode and run, or:

```bash
cd DecisionEngine
swift build
swift run
```

## Usage

1. Launch the app
2. Enter beneficiary names (comma-separated)
3. Drop files/folders into the drop zone
4. Click "Start Analysis"
5. View progress and await results
6. Copy or save the strategic report

## Architecture

```
DecisionEngine/
├── DecisionEngine/          # SwiftUI Frontend
│   ├── App/                # Main app entry
│   ├── Views/              # SwiftUI views
│   ├── Models/             # Data models
│   └── Services/           # Python bridge
├── backend/                # Python Backend
│   ├── agents/             # Multi-agent system
│   ├── ingestion/          # File processing
│   ├── memory/             # ChromaDB vector store
│   ├── llm/                # LLM wrappers
│   └── output/             # Report generation
└── agents/                  # Agent profiles (markdown)
```

## Supported File Types

| Type | Extensions | Processing |
|------|------------|------------|
| Text | .txt, .md, .json | Direct extraction |
| Documents | .pdf, .docx | PDF/DOCX parsing |
| Email | .eml, .msg | Header + body extraction |
| Images | .jpg, .png | OCR via Vision/Tesseract |
| Video | .mp4, .mov | Audio extraction + transcription |
| Audio | .mp3, .wav | MLX-Whisper transcription |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/llm/status` | GET | LLM provider status |
| `/analyze` | POST | Start analysis |
| `/status/{task_id}` | GET | Get task status |
| `/result/{task_id}` | GET | Get analysis result |

## Configuration

See `.env.example` for configuration options:

- `GEMINI_API_KEY` - Google Gemini API
- `OPENAI_API_KEY` - OpenAI API (optional)
- `USE_LLM` - Enable/disable LLM (default: true)
- `DEBATE_ROUNDS` - Agent debate rounds (default: 2)

## Agent Personas

Each agent has three profile files:

- **IDENTITY.md**: Core identity and purpose
- **SKILLS.md**: Technical capabilities
- **SOUL.md**: Philosophical stance and values

Agents can be customized by editing their markdown profiles in `agents/<agent_name>/`.

## License

MIT
