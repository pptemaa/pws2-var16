"""Пять демонстраций преобразования MP3 в WAV без бинарных файлов в git."""

import subprocess
import wave
from io import BytesIO

import imageio_ffmpeg

from src.convert import convert_mp3

CASES = (
    (440, 0.2),
    (523, 0.3),
    (659, 0.4),
    (784, 0.5),
    (880, 0.6),
)


def make_mp3(frequency, duration):
    """Сгенерировать тестовый MP3 с синусоидальным сигналом."""
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel",
               "error", "-f", "lavfi", "-i",
               f"sine=frequency={frequency}:duration={duration}",
               "-f", "mp3", "pipe:1"]
    return subprocess.run(command, capture_output=True, check=True).stdout


def main():
    """Напечатать пять параметров входа и характеристики выходного WAV."""
    for number, (frequency, duration) in enumerate(CASES, 1):
        source = make_mp3(frequency, duration)
        output = convert_mp3(source)
        with wave.open(BytesIO(output), "rb") as wav:
            print(number, frequency, duration, len(source), len(output),
                  wav.getnchannels(), wav.getframerate(), wav.getnframes())


if __name__ == "__main__":
    main()
