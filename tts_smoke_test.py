import asyncio
import os

from audio_engine import AudioEngine


async def main() -> None:
    engine = AudioEngine.__new__(AudioEngine)
    engine.voice = "pt-BR-FranciscaNeural"
    engine._last_tts_provider = None
    audio_path = None

    try:
        audio_path = await engine._generate_audio("Estou ouvindo.")
        print(
            f"Síntese concluída por {engine._last_tts_provider}; "
            f"arquivo gerado com {os.path.getsize(audio_path)} bytes."
        )
    except Exception as exc:
        print(f"Síntese falhou: {type(exc).__name__}.")
        raise
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


if __name__ == "__main__":
    asyncio.run(main())
