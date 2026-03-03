import { GoogleGenAI } from '@google/genai';

const USE_PYTHON_BACKEND = import.meta.env.VITE_USE_PYTHON_BACKEND === 'true';
const BACKEND_URL = import.meta.env.VITE_BACKEND_PORT 
  ? `http://localhost:${import.meta.env.VITE_BACKEND_PORT}` 
  : 'http://localhost:8000';

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_CUSTOM_GEMINI_KEY });

export async function getWittyResponse(objective: string) {
  // If using Python backend, route through it
  if (USE_PYTHON_BACKEND) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/agent/witty`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective })
      });
      if (response.ok) {
        const data = await response.json();
        return data.response;
      }
    } catch (e) {
      console.warn('Backend witty response failed, falling back to direct Gemini:', e);
    }
  }
  
  // Fallback to direct Gemini call
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `The user stated their objective: "${objective}". Give a very short, witty, grayscale-themed, slightly cynical but helpful response (max 15 words) inviting them to drop their files to achieve this.`,
    });
    return response.text || "Drop your files. Let's sort this mess out.";
  } catch (error) {
    console.error(error);
    return "Drop your files. Let's sort this mess out.";
  }
}
