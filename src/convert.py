"""Преобразование потока MP3 из stdin в поток WAV на stdout."""

import subprocess
import sys
import wave
from io import BytesIO

import imageio_ffmpeg


def convert_mp3(data):
    """Вернуть WAV PCM для переданного потока MP3."""
    if not data:
        raise ValueError("Пустой поток MP3")
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
        "-ac", "1", "-ar", "44100", "-f", "s16le", "pipe:1",
    ]
    result = subprocess.run(command, input=data, capture_output=True,
                            check=False)
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(error or "Ошибка преобразования MP3")
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(result.stdout)
    return output.getvalue()


def main():
    """Считать MP3 и записать WAV без текстовых сообщений в stdout."""
    try:
        sys.stdout.buffer.write(convert_mp3(sys.stdin.buffer.read()))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
