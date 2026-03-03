# Gemini API

The fastest path from prompt to production with Gemini, Veo, Nano Banana, and more.

### Python

    from google import genai

    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Explain how AI works in a few words",
    )

    print(response.text)

### JavaScript

    import { GoogleGenAI } from "@google/genai";

    const ai = new GoogleGenAI({});

    async function main() {
      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: "Explain how AI works in a few words",
      });
      console.log(response.text);
    }

    await main();

### Go

    package main

    import (
        "context"
        "fmt"
        "log"
        "google.golang.org/genai"
    )

    func main() {
        ctx := context.Background()
        client, err := genai.NewClient(ctx, nil)
        if err != nil {
            log.Fatal(err)
        }

        result, err := client.Models.GenerateContent(
            ctx,
            "gemini-3-flash-preview",
            genai.Text("Explain how AI works in a few words"),
            nil,
        )
        if err != nil {
            log.Fatal(err)
        }
        fmt.Println(result.Text())
    }

### Java

    package com.example;

    import com.google.genai.Client;
    import com.google.genai.types.GenerateContentResponse;

    public class GenerateTextFromTextInput {
      public static void main(String[] args) {
        Client client = new Client();

        GenerateContentResponse response =
            client.models.generateContent(
                "gemini-3-flash-preview",
                "Explain how AI works in a few words",
                null);

        System.out.println(response.text());
      }
    }

### C#

    using System.Threading.Tasks;
    using Google.GenAI;
    using Google.GenAI.Types;

    public class GenerateContentSimpleText {
      public static async Task main() {
        var client = new Client();
        var response = await client.Models.GenerateContentAsync(
          model: "gemini-3-flash-preview", contents: "Explain how AI works in a few words"
        );
        Console.WriteLine(response.Candidates[0].Content.Parts[0].Text);
      }
    }

### REST

    curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -H 'Content-Type: application/json' \
      -X POST \
      -d '{
        "contents": [
          {
            "parts": [
              {
                "text": "Explain how AI works in a few words"
              }
            ]
          }
        ]
      }'

[Start building](https://ai.google.dev/gemini-api/docs/quickstart) Follow our Quickstart guide to get an API key and make your first API call in minutes.

*** ** * ** ***

## Meet the models

[View all](https://ai.google.dev/gemini-api/docs/models) [Gemini 3.1 Pro
New
Our most intelligent model, the best in the world for multimodal understanding, all built on state-of-the-art reasoning.](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview) [Gemini 3 Flash
New
Frontier-class performance rivaling larger models at a fraction of the cost.](https://ai.google.dev/gemini-api/docs/models/gemini-3-flash-preview) [Nano Banana 2 and Nano Banana Pro
State-of-the-art image generation and editing models.](https://ai.google.dev/gemini-api/docs/image-generation) [Veo 3.1
Our state-of-the-art video generation model, with native audio.](https://ai.google.dev/gemini-api/docs/video) [Gemini 2.5 Pro TTS
Gemini 2.5 model variant with native text-to-speech (TTS) capabilities.](https://ai.google.dev/gemini-api/docs/speech-generation) [Gemini Robotics
A vision-language model (VLM) that brings Gemini's agentic capabilities to robotics and enables advanced reasoning in the physical world.](https://ai.google.dev/gemini-api/docs/robotics-overview)

## Explore Capabilities

[Native Image Generation (Nano Banana)
Generate and edit highly contextual images natively with Gemini 2.5 Flash Image.](https://ai.google.dev/gemini-api/docs/image-generation) [Long Context
Input millions of tokens to Gemini models and derive understanding from unstructured images, videos, and documents.](https://ai.google.dev/gemini-api/docs/long-context) [Structured Outputs
Constrain Gemini to respond with JSON, a structured data format suitable for automated processing.](https://ai.google.dev/gemini-api/docs/structured-output) [Function Calling
Build agentic workflows by connecting Gemini to external APIs and tools.](https://ai.google.dev/gemini-api/docs/function-calling) [Video Generation with Veo 3.1
Create high-quality video content from text or image prompts with our state-of-the-art model.](https://ai.google.dev/gemini-api/docs/video) [Voice Agents with Live API
Build real-time voice applications and agents with the Live API.](https://ai.google.dev/gemini-api/docs/live) [Tools
Connect Gemini to the world through built-in tools like Google Search, URL Context, Google Maps, Code Execution and Computer Use.](https://ai.google.dev/gemini-api/docs/tools) [Document Understanding
Process up to 1000 pages of PDF files with full multimodal understanding or other text-based file types.](https://ai.google.dev/gemini-api/docs/document-processing) [Thinking
Explore how thinking capabilities improve reasoning for complex tasks and agents.](https://ai.google.dev/gemini-api/docs/thinking) [Google AI Studio
Test prompts, manage your API keys, monitor usage, and build prototypes.](https://aistudio.google.com) [Developer Community
Ask questions and find solutions from other developers and Google engineers.](https://discuss.ai.google.dev/c/gemini-api/4) [API Reference
Find detailed information about the Gemini API in the official reference documentation.](https://ai.google.dev/api) [Status
Check the status of Gemini API, Google AI Studio, and our model services.](https://aistudio.google.com/status)

<br />

Built to refine the performance and reliability of the Gemini 3 Pro series,
Gemini 3.1 Pro Preview provides better thinking, improved token
efficiency, and a more grounded, factually consistent experience. It's optimized
for software engineering behavior and usability, as well as agentic workflows
requiring precise tool usage and reliable multi-step execution across real-world
domains.
[Try in Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-3.1-pro-preview)

## Documentation

Visit the [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3) page for full
coverage of features and capabilities.

## gemini-3.1-pro-preview

| Property | Description |
|---|---|
| Model code | `gemini-3.1-pro-preview` |
| Supported data types | **Inputs** Text, Image, Video, Audio, and PDF **Output** Text |
| Token limits^[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens)^ | **Input token limit** 1,048,576 **Output token limit** 65,536 |
| Capabilities | **Audio generation** Not supported **Batch API** Supported **Caching** Supported **Code execution** Supported **File search** Supported (AI Studio only) **Function calling** Supported **Grounding with Google Maps** Not supported **Image generation** Not supported **Live API** Not supported **Search grounding** Supported **Structured outputs** Supported **Thinking** Supported **URL context** Supported |
| Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details. - Preview: `gemini-3.1-pro-preview` - Preview: `gemini-3.1-pro-preview-customtools` \* |
| Latest update | February 2026 |
| Knowledge cutoff | January 2025 |

#### gemini-3.1-pro-preview-customtools

\* *For those building with a mix of bash and custom tools, Gemini 3.1 Pro Preview
comes with a separate endpoint available via the API called
`gemini-3.1-pro-preview-customtools`. This endpoint is better at prioritizing
your custom tools (for example `view_file` or `search_code`).*

*Note that while `gemini-3.1-pro-preview-customtools` is optimized for agentic
workflows that use custom tools and bash, you may see quality fluctuations in
some use cases which don't benefit from such tools.*

<br />

The best model in the world for multimodal understanding, and our most powerful
agentic and vibe-coding model yet, delivering richer visuals and deeper
interactivity, all built on a foundation of state-of-the-art reasoning.
[Try in Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-3-flash-preview)

## Documentation

Visit the [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3) page for full coverage of
features and capabilities.

## gemini-3-flash-preview

| Property | Description |
|---|---|
| Model code | `gemini-3-flash-preview` |
| Supported data types | **Inputs** Text, Image, Video, Audio, and PDF **Output** Text |
| Token limits^[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens)^ | **Input token limit** 1,048,576 **Output token limit** 65,536 |
| Capabilities | **Audio generation** Not supported **Batch API** Supported **Caching** Supported **Code execution** Supported **Computer use** Supported **File search** Supported **Function calling** Supported **Grounding with Google Maps** Not supported **Image generation** Not supported **Live API** Not supported **Search grounding** Supported **Structured outputs** Supported **Thinking** Supported **URL context** Supported |
| Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details. - `Preview: gemini-3-flash-preview` |
| Latest update | December 2025 |
| Knowledge cutoff | January 2025 |

<br />

**Nano Banana 2** provides high-quality image generation and conversational
editing at a mainstream price point and low latency. It serves as the
high-efficiency counterpart to [Gemini 3 Pro Image](https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image-preview), optimized for speed and
high-volume developer use cases.

**Key updates:**

- New output resolution options:
  - New support for 0.5K, 2K and 4K, default 1K
- New Image Search Grounding:
  - Integration of both text and image search results to inform generation with real-time web data
  - Supported with Thinking on or off
- New 1:4, 4:1, 1:8 and 8:1 aspect ratios
- Improved aspect ratio adherence
- Improved image quality and consistency
- Improved i18n text rendering

[Try in Google AI Studio](https://aistudio.google.com?model=gemini-3.1-flash-image-preview)

## Documentation

Visit the [Image generation](https://ai.google.dev/gemini-api/docs/image-generation) page for full
coverage of features and capabilities.

## gemini-3.1-flash-image-preview

| Property | Description |
|---|---|
| Model code | `gemini-3.1-flash-image-preview` |
| Supported data types | **Inputs** Text and Image / PDF **Output** Image and Text |
| Token limits^[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens)^ | **Input token limit** 131,072 **Output token limit** 32,768 |
| Capabilities | **Audio generation** Not supported **Batch API** Supported **Caching** Not supported **Code execution** Not supported **File search** Not supported **Function calling** Not supported **Grounding with Google Maps** Not supported **Image generation** Supported **Live API** Not supported **Search grounding** Supported **Structured outputs** Not supported **Thinking** Supported **URL context** Not supported |
| Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details. - `Preview: gemini-3.1-flash-image-preview` |
| Latest update | February 2026 |
| Knowledge cutoff | January 2025 |

<br />

The Live API enables low-latency, real-time voice and video interactions with
Gemini 2.5 Flash. It processes continuous streams of audio, video, or text to
deliver immediate, human-like spoken responses, creating a natural
conversational experience for your users.
[Try in Google AI Studio](https://aistudio.google.com?model=gemini-2.5-flash-native-audio-preview-12-2025)

## Documentation

Visit the [Live API](https://ai.google.dev/gemini-api/docs/live) guide for full coverage
of features and capabilities.

## gemini-2.5-flash-native-audio-preview-12-2025

| Property | Description |
|---|---|
| Model code | `gemini-2.5-flash-native-audio-preview-12-2025` |
| Supported data types | **Inputs** Audio, video, text **Output** Audio and text |
| Token limits^[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens)^ | **Input token limit** 131,072 **Output token limit** 8,192 |
| Capabilities | **Audio generation** Supported **Batch API** Not supported **Caching** Not supported **Code execution** Not supported **File search** Not Supported **Function calling** Supported **Grounding with Google Maps** Not supported **Image generation** Not supported **Live API** Supported **Search grounding** Supported **Structured outputs** Not supported **Thinking** Supported **URL context** Not supported |
| Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details. - Preview: `gemini-2.5-flash-native-audio-preview-12-2025` - Preview: `gemini-2.5-flash-native-audio-preview-09-2025` |
| Latest update | September 2025 |
| Knowledge cutoff | January 2025 |

