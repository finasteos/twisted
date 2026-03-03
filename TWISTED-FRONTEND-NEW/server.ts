import express from "express";
import { createServer as createViteServer } from "vite";
import { WebSocketServer, WebSocket } from "ws";
import http from "http";
import { GoogleGenAI, Type } from "@google/genai";
import { tavily } from "@tavily/core";
import FirecrawlApp from "@mendable/firecrawl-js";
import { QdrantClient } from "@qdrant/js-client-rest";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/ws/cases" });
const PORT = 3000;

// Python backend proxy settings
const USE_PYTHON_BACKEND = process.env.VITE_USE_PYTHON_BACKEND === 'true';
const PYTHON_BACKEND_URL = process.env.VITE_BACKEND_PORT 
  ? `http://localhost:${process.env.VITE_BACKEND_PORT}` 
  : 'http://localhost:8000';

// Proxy helper
async function proxyToPythonBackend(reqPath: string, options: any = {}) {
  if (!USE_PYTHON_BACKEND) return null;
  try {
    const url = `${PYTHON_BACKEND_URL}${reqPath}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return await response.json();
  } catch (e) {
    console.error(`Proxy error for ${reqPath}:`, e);
    return null;
  }
}

app.use(express.json());

// Initialize AI clients lazily
let ai: GoogleGenAI | null = null;
let tvly: any = null;
let firecrawl: any = null;
let qdrant: QdrantClient | null = null;

let agentConfig = [
  { id: 'coordinator', name: 'Coordinator Alpha', model: 'gemini-3-flash-preview', prompt: 'You orchestrate the swarm...', temperature: 0.7 },
  { id: 'context_weaver', name: 'Context Weaver', model: 'gemini-3.1-pro-preview', prompt: 'Extract key entities, locations, people, and the core problem from this query: "{{query}}". Return JSON with keys: entities (array), problem (string).', temperature: 0.7 },
  { id: 'echo_vault', name: 'Echo Vault', model: 'gemini-3.1-pro-preview', prompt: 'You recall past cases and search the web...', temperature: 0.7 },
  { id: 'outcome_architect', name: 'Outcome Architect', model: 'gemini-3.1-pro-preview', prompt: 'You are a strategic advisor. Given the specific problem: "{{problem}}", and the following research context: "{{research}}", devise a highly relevant, concrete 3-step strategy to resolve THIS SPECIFIC issue. Ignore any past cases in the research that are not directly applicable to the current problem.', temperature: 0.7 },
  { id: 'chronicle_scribe', name: 'Chronicle Scribe', model: 'gemini-3.1-pro-preview', prompt: 'Create a final report based on this strategy: {{strategy}}. Return JSON with: strategic_report (markdown string), emails (array of {subject, body}), contacts (array of {name, role, organization, priority, contact_methods}).', temperature: 0.7 },
];

function getAI() {
  if (!ai) {
    const key = process.env.VITE_CUSTOM_GEMINI_KEY || process.env.GEMINI_API_KEY;
    if (!key) throw new Error("Missing Gemini API Key");
    ai = new GoogleGenAI({ apiKey: key });
  }
  return ai;
}

function getTavily() {
  if (!tvly && process.env.VITE_TAVILY_API_KEY) {
    tvly = tavily({ apiKey: process.env.VITE_TAVILY_API_KEY });
  }
  return tvly;
}

function getFirecrawl() {
  if (!firecrawl && process.env.VITE_FIRECRAWL_KEY) {
    firecrawl = new FirecrawlApp({ apiKey: process.env.VITE_FIRECRAWL_KEY });
  }
  return firecrawl;
}

function parseJSONResponse(text: string | undefined): any {
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (e) {
    const match = text.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        return JSON.parse(match[0]);
      } catch (e2) {
        console.error("Failed to parse extracted JSON:", match[0]);
        return {};
      }
    }
    console.error("No JSON object found in response:", text);
    return {};
  }
}

function getQdrant() {
  if (!qdrant && process.env.VITE_QDRANT_URL && process.env.VITE_QDRANT_API_KEY) {
    qdrant = new QdrantClient({
      url: process.env.VITE_QDRANT_URL,
      apiKey: process.env.VITE_QDRANT_API_KEY,
    });
  }
  return qdrant;
}

// Ensure Qdrant collection exists
async function ensureQdrantCollection() {
  const client = getQdrant();
  if (!client) return;
  try {
    const collections = await client.getCollections();
    const exists = collections.collections.some(c => c.name === "past_cases");
    if (!exists) {
      await client.createCollection("past_cases", {
        vectors: {
          size: 768, // Gemini text-embedding-004 size
          distance: "Cosine"
        }
      });
      console.log("Created Qdrant collection: past_cases");
    }
  } catch (e) {
    console.error("Failed to ensure Qdrant collection:", e);
  }
}

// Call it once on startup
ensureQdrantCollection();

// API routes
app.get("/api/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/api/admin/qdrant", async (req, res) => {
  const qdrantClient = getQdrant();
  if (!qdrantClient) {
    return res.json({ status: "Not Configured", points_count: 0 });
  }
  try {
    const collectionInfo = await qdrantClient.getCollection("past_cases");
    res.json({ 
      status: collectionInfo.status, 
      points_count: collectionInfo.points_count 
    });
  } catch (e: any) {
    res.json({ status: "Error", points_count: 0, error: e.message });
  }
});

app.delete("/api/admin/qdrant", async (req, res) => {
  const qdrantClient = getQdrant();
  if (!qdrantClient) {
    return res.status(400).json({ error: "Qdrant not configured" });
  }
  try {
    await qdrantClient.deleteCollection("past_cases");
    await ensureQdrantCollection();
    res.json({ success: true, message: "Memory cleared" });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

app.get("/api/admin/agents", (req, res) => {
  res.json(agentConfig);
});

app.post("/api/admin/agents", (req, res) => {
  if (Array.isArray(req.body)) {
    agentConfig = req.body;
    res.json({ status: "ok" });
  } else {
    res.status(400).json({ error: "Invalid payload" });
  }
});

app.post("/api/knowledge", async (req, res) => {
  const { text, title } = req.body;
  const qdrantClient = getQdrant();
  const genai = getAI();
  
  if (!qdrantClient) {
    return res.status(400).json({ error: "Qdrant not configured" });
  }
  
  try {
    const embedRes = await genai.models.embedContent({
      model: "gemini-embedding-001",
      contents: text
    });
    
    const vector = embedRes.embeddings?.[0]?.values;
    if (vector) {
      await qdrantClient.upsert("past_cases", {
        wait: true,
        points: [
          {
            id: Date.now().toString(),
            vector: vector,
            payload: {
              problem: `Knowledge Base: ${title}`,
              strategy: text,
              timestamp: new Date().toISOString(),
              type: "knowledge"
            }
          }
        ]
      });
      res.json({ success: true });
    } else {
      res.status(500).json({ error: "Failed to generate embedding" });
    }
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

// WebSocket logic for swarm debate
wss.on("connection", (ws: WebSocket, req) => {
  console.log("Client connected to WebSocket");
  
  ws.on("message", async (message) => {
    try {
      const data = JSON.parse(message.toString());
      if (data.type === "START_ANALYSIS") {
        await runSwarmAnalysis(ws, data.payload);
      }
    } catch (err) {
      console.error("Error processing message:", err);
    }
  });

  ws.on("close", () => {
    console.log("Client disconnected");
  });
});

async function runSwarmAnalysis(ws: WebSocket, payload: any) {
  const { query, deepResearch } = payload;
  const model = deepResearch ? "gemini-3.1-pro-preview" : "gemini-3-flash-preview";
  const genai = getAI();
  
  const sendEvent = (level: string, agent: string, msg: string, metadata?: any) => {
    ws.send(JSON.stringify({
      type: "EVENT_LOG",
      payload: {
        id: Date.now().toString() + Math.random(),
        timestamp: Date.now(),
        level,
        agent,
        message: msg,
        metadata
      }
    }));
  };

  const sendAgentThought = (agentId: string, state: string, thoughtQuery: string, confidence: number) => {
    ws.send(JSON.stringify({
      type: "AGENT_THOUGHT",
      payload: {
        agentId,
        state,
        query: thoughtQuery,
        evidence: [],
        confidence,
        timestamp: Date.now()
      }
    }));
  };

  const sendProgress = (stage: string, percent: number, msg: string) => {
    ws.send(JSON.stringify({
      type: "PROGRESS",
      payload: { stage, percent, message: msg }
    }));
  };

  const sendTokenUsage = (agentId: string, usage: any) => {
    if (!usage) return;
    ws.send(JSON.stringify({
      type: "TOKEN_USAGE",
      payload: {
        agentId,
        promptTokens: usage.promptTokenCount || 0,
        completionTokens: usage.candidatesTokenCount || 0,
        totalTokens: usage.totalTokenCount || 0
      }
    }));
  };

  try {
    sendAgentThought("coordinator", "reasoning", "Initializing swarm debate protocol...", 0.1);
    sendAgentThought("pulse_monitor", "active", "Establishing telemetry streams...", 1.0);
    sendEvent("INFO", "Coordinator Alpha", `Swarm initialized. Deep Research: ${deepResearch ? 'ENABLED' : 'DISABLED'}.`);
    sendProgress("Ingestion", 5, "Ingesting initial query");
    
    // Step 1: Context Weaver extracts entities
    sendAgentThought("coordinator", "reasoning", "Delegating entity extraction to Context Weaver...", 0.2);
    sendAgentThought("context_weaver", "querying", "Parsing query for entities and core problem...", 0.3);
    sendEvent("THINK", "Context Weaver", "Analyzing the provided query to extract entities and intent.");
    
    const cwConfig = agentConfig.find(a => a.id === 'context_weaver');
    const extractionPrompt = cwConfig?.prompt.replace('{{query}}', query) || `Extract key entities, locations, people, and the core problem from this query: "${query}". Return JSON with keys: entities (array), problem (string).`;
    const extractionRes = await genai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: extractionPrompt,
      config: { 
        responseMimeType: "application/json",
        temperature: cwConfig?.temperature || 0.7
      }
    });
    sendTokenUsage("context_weaver", extractionRes.usageMetadata);
    
    const extracted = parseJSONResponse(extractionRes.text);
    sendAgentThought("context_weaver", "complete", "Extraction complete.", 1.0);
    sendEvent("SUCCESS", "Context Weaver", `Extracted entities: ${extracted.entities?.join(", ")}`, extracted);
    sendProgress("Analysis", 25, "Entities extracted");

    // Step 2: Echo Vault performs research
    sendAgentThought("coordinator", "reasoning", "Routing extracted entities to Echo Vault for deep web research and memory retrieval...", 0.4);
    sendAgentThought("echo_vault", "querying", "Scanning external knowledge bases, live web, and past cases...", 0.5);
    sendEvent("INFO", "Echo Vault", "Initiating search for relevant information and past cases.");
    
    let researchResults = "";
    
    // 2a. Query Qdrant for past cases
    const qdrantClient = getQdrant();
    if (qdrantClient) {
      sendEvent("THINK", "Echo Vault", "Querying Qdrant Vector Memory for similar past cases.");
      try {
        const embedRes = await genai.models.embedContent({
          model: "text-embedding-004",
          contents: extracted.problem || query
        });
        const vector = embedRes.embeddings?.[0]?.values;
        if (vector) {
          const searchRes = await qdrantClient.search("past_cases", {
            vector: vector,
            limit: 3,
            with_payload: true,
            score_threshold: 0.65
          });
          if (searchRes.length > 0) {
            researchResults += "### Similar Past Cases\\n";
            searchRes.forEach((match: any) => {
              researchResults += `- **Problem**: ${match.payload.problem}\\n  **Strategy**: ${match.payload.strategy}\\n\\n`;
            });
            sendEvent("SUCCESS", "Echo Vault", `Retrieved ${searchRes.length} similar past cases from memory.`);
          } else {
            sendEvent("INFO", "Echo Vault", "No similar past cases found in memory.");
          }
        }
      } catch (e: any) {
        sendEvent("WARNING", "Echo Vault", `Qdrant memory retrieval failed: ${e.message}`);
      }
    } else {
      sendEvent("WARNING", "Echo Vault", "Qdrant Vector Memory not configured. Skipping past cases retrieval.");
    }

    // 2b. Query Tavily for live web context
    const tavilyClient = getTavily();
    if (tavilyClient) {
      sendEvent("THINK", "Echo Vault", "Using Tavily Search API for deep context retrieval.");
      try {
        const searchRes = await tavilyClient.search(query, { searchDepth: "advanced" });
        researchResults += "### Live Web Context\\n";
        researchResults += searchRes.results.map((r: any) => `[${r.title}](${r.url}): ${r.content}`).join("\\n");
        sendEvent("SUCCESS", "Echo Vault", "Retrieved context from Tavily.", { resultsCount: searchRes.results.length });
      } catch (e: any) {
        sendEvent("WARNING", "Echo Vault", `Tavily search failed: ${e.message}`);
      }
    } else {
      sendEvent("WARNING", "Echo Vault", "Tavily API key missing. Falling back to internal knowledge.");
      if (!researchResults) researchResults = "No external search performed.";
    }
    sendAgentThought("echo_vault", "complete", "Research phase concluded.", 1.0);
    sendProgress("Analysis", 50, "Research complete");

    // Step 3: Outcome Architect devises strategy
    sendAgentThought("coordinator", "reasoning", "Aggregating research and prompting Outcome Architect...", 0.6);
    sendAgentThought("outcome_architect", "reasoning", "Synthesizing research into strategic options...", 0.7);
    sendEvent("THINK", "Outcome Architect", "Developing hypotheses and strategic approaches based on gathered evidence.");
    
    const oaConfig = agentConfig.find(a => a.id === 'outcome_architect');
    const strategyPrompt = oaConfig?.prompt.replace('{{problem}}', extracted.problem || '').replace('{{research}}', researchResults) || `You are a strategic advisor. Given the specific problem: "${extracted.problem}", and the following research context: "${researchResults}", devise a highly relevant, concrete 3-step strategy to resolve THIS SPECIFIC issue. Ignore any past cases in the research that are not directly applicable to the current problem.`;
    const strategyRes = await genai.models.generateContent({
      model,
      contents: strategyPrompt,
      config: {
        temperature: oaConfig?.temperature || 0.7
      }
    });
    sendTokenUsage("outcome_architect", strategyRes.usageMetadata);
    
    sendAgentThought("outcome_architect", "complete", "Strategy formulated.", 1.0);
    sendEvent("SUCCESS", "Outcome Architect", "Strategy formulated.", { strategy: strategyRes.text });
    sendProgress("Debate", 75, "Strategy formulated");

    // Step 4: Chronicle Scribe drafts final deliverables
    sendAgentThought("coordinator", "reasoning", "Directing Chronicle Scribe to draft final deliverables...", 0.8);
    sendAgentThought("chronicle_scribe", "reasoning", "Drafting final reports and communications...", 0.9);
    sendEvent("THINK", "Chronicle Scribe", "Formatting the strategy into actionable deliverables.");
    
    const csConfig = agentConfig.find(a => a.id === 'chronicle_scribe');
    const reportPrompt = csConfig?.prompt.replace('{{strategy}}', strategyRes.text || '') || `Create a final report based on this strategy: ${strategyRes.text}. Return JSON with: strategic_report (markdown string), emails (array of {subject, body}), contacts (array of {name, role, organization, priority, contact_methods}).`;
    
    const reportRes = await genai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: reportPrompt,
      config: { 
        responseMimeType: "application/json",
        temperature: csConfig?.temperature || 0.7
      }
    });
    sendTokenUsage("chronicle_scribe", reportRes.usageMetadata);
    
    const deliverables = parseJSONResponse(reportRes.text);
    sendAgentThought("chronicle_scribe", "complete", "Deliverables finalized.", 1.0);
    sendEvent("SUCCESS", "Chronicle Scribe", "Deliverables finalized.");
    
    // Step 5: Save new case to Qdrant memory
    if (qdrantClient && extracted.problem && strategyRes.text) {
      sendEvent("THINK", "Echo Vault", "Committing new case to Vector Memory...");
      try {
        const embedRes = await genai.models.embedContent({
          model: "text-embedding-004",
          contents: extracted.problem
        });
        const vector = embedRes.embeddings?.[0]?.values;
        if (vector) {
          await qdrantClient.upsert("past_cases", {
            wait: true,
            points: [
              {
                id: Date.now().toString(), // Use timestamp as simple ID
                vector: vector,
                payload: {
                  problem: extracted.problem,
                  strategy: strategyRes.text,
                  timestamp: new Date().toISOString()
                }
              }
            ]
          });
          sendEvent("SUCCESS", "Echo Vault", "Case successfully committed to Vector Memory.");
        }
      } catch (e: any) {
        sendEvent("WARNING", "Echo Vault", `Failed to commit case to memory: ${e.message}`);
      }
    }
    
    sendAgentThought("coordinator", "complete", "Swarm consensus reached. Operations concluded.", 1.0);
    sendAgentThought("pulse_monitor", "complete", "Telemetry finalized. All systems nominal.", 1.0);
    sendProgress("Synthesis", 100, "Analysis complete");

    ws.send(JSON.stringify({
      type: "COMPLETE",
      payload: deliverables
    }));

  } catch (error: any) {
    console.error("Swarm error:", error);
    sendEvent("ERROR", "System", `Fatal error during swarm execution: ${error.message}`);
    ws.send(JSON.stringify({ type: "ERROR", payload: error.message }));
  }
}

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static("dist"));
  }

  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
