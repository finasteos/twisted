"""
Video Parser - Audio extraction and transcription
"""

from pathlib import Path
import asyncio
from backend.utils.mlx_utils import cleanup_model


async def extract_video(path: Path) -> str:
    """Extract audio from video and transcribe."""
    await asyncio.sleep(0.3)

    try:
        from moviepy.editor import VideoFileClip

        temp_audio = path.with_suffix(".wav")

        video = VideoFileClip(str(path))
        video.audio.write_audiofile(str(temp_audio), verbose=False, logger=None)
        video.close()

        transcription = await transcribe_audio(temp_audio)

        if temp_audio.exists():
            temp_audio.unlink()

        return transcription
    except Exception as e:
        return f"[Video transcription failed: {e}]"


async def transcribe_audio(audio_path: Path) -> str:
    """Transcribe audio file using MLX-Whisper or Gemini Flash fallback."""
    from backend.config.settings import settings
    from backend.main import gemini_wrapper

    if settings.DISABLE_LOCAL_MLX and gemini_wrapper:
        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

                response = await gemini_wrapper.generate(
                    contents=[
                        {"mime_type": "audio/wav", "data": audio_data},
                        {"text": "Transcribe this audio file accurately. Return only the transcription text."}
                    ],
                    task_complexity="analysis"
                )
            text_content = getattr(response, 'text', getattr(response, 'content', str(response)))
            return f"[Gemini Flash Transcription]\n{text_content}"
        except Exception as e:
            print(f"Gemini video-audio transcription failed: {e}")

    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path))

        text = result["text"]

        # Use centralized memory cleanup
        cleanup_model(model)

        return text
    except Exception as e:
        return f"[Audio transcription failed: {e}]"
