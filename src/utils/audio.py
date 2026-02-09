"""
Audio processing utilities
"""

import logging
import subprocess
from pathlib import Path

from src.config import DEFAULT_HEADERS

logger = logging.getLogger(__name__)


def convert_to_wav(
    link: str, output_file: Path, sample_rate: int = 16000, channels: int = 1
) -> bool:
    """
    Convert audio file to WAV format with specified parameters

    Args:
        input_file: Path to input audio file
        output_file: Path to output WAV file
        sample_rate: Target sample rate in Hz (default: 16000)
        channels: Number of audio channels (default: 1 for mono)

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Build ffmpeg command with User-Agent and Referer for URLs that require them
        cmd = [
            "ffmpeg",
            "-user_agent",
            DEFAULT_HEADERS["User-Agent"],
            "-referer",
            DEFAULT_HEADERS["Referer"],
            "-i",
            link,
            "-acodec",
            "pcm_s16le",  # 16-bit PCM
            "-ar",
            str(sample_rate),  # Sample rate
            "-ac",
            str(channels),  # Channels
            "-y",  # Overwrite output file
            str(output_file),
        ]

        # Run conversion
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True

    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False


def extract_audio_from_video(
    video_file: Path, audio_file: Path, sample_rate: int = 16000, channels: int = 1
) -> bool:
    """
    Extract audio from video file and save as WAV

    Args:
        video_file: Path to input video file
        audio_file: Path to output audio file
        sample_rate: Target sample rate in Hz (default: 16000)
        channels: Number of audio channels (default: 1 for mono)

    Returns:
        True if extraction successful, False otherwise
    """
    try:
        # Build ffmpeg command for extraction
        cmd = [
            "ffmpeg",
            "-i",
            str(video_file),
            "-vn",  # No video
            "-acodec",
            "pcm_s16le",  # 16-bit PCM
            "-ar",
            str(sample_rate),
            "-ac",
            str(channels),
            "-y",
            str(audio_file),
        ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)

        return True

    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False


def get_audio_duration(audio_file: Path) -> float | None:
    """
    Get duration of audio file in seconds

    Args:
        audio_file: Path to audio file

    Returns:
        Duration in seconds, or None if error
    """
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        duration = float(result.stdout.strip())
        return duration

    except (subprocess.CalledProcessError, ValueError):
        return None
    except FileNotFoundError:
        return None


def get_audio_info(audio_file: Path) -> tuple[int, int, float] | None:
    """
    Get audio file information

    Args:
        audio_file: Path to audio file

    Returns:
        Tuple of (sample_rate, channels, duration) or None if error
    """
    try:
        # Get format info
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels,duration",
            "-of",
            "default=noprint_wrappers=1",
            str(audio_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse output
        info = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info[key] = value

        sample_rate = int(info.get("sample_rate", 0))
        channels = int(info.get("channels", 0))
        duration = float(info.get("duration", 0))

        return (sample_rate, channels, duration)

    except Exception:
        return None


def normalize_audio_file(
    input_file: Path,
    output_file: Path | None = None,
    sample_rate: int = 16000,
    channels: int = 1,
) -> bool:
    """
    Normalize audio file to standard format (16-bit WAV, 16kHz, mono)

    Args:
        input_file: Path to input audio file
        output_file: Path to output file (if None, overwrites input)
        sample_rate: Target sample rate (default: 16000)
        channels: Number of channels (default: 1)

    Returns:
        True if successful, False otherwise
    """
    if output_file is None:
        output_file = input_file

    # Create temp file if overwriting
    if output_file == input_file:
        temp_file = input_file.with_suffix(".tmp.wav")
        success = convert_to_wav(input_file, temp_file, sample_rate, channels)
        if success:
            temp_file.replace(input_file)
        return success
    else:
        return convert_to_wav(input_file, output_file, sample_rate, channels)
