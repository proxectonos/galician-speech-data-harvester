"""
Base downloader class for all data sources
"""

import json
import logging
import subprocess
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from typing import Any, NamedTuple
from venv import logger

import requests

from src.utils.audio import get_audio_duration

from .config import DEFAULT_HEADERS, DEFAULT_TIMEOUT, MAX_RETRIES, WORKERS, get_headers


class BaseDownloader(ABC):
    """Abstract base class for all downloaders"""

    def __init__(self, output_dir: str, logger: logging.Logger | None = None):
        """
        Initialize the downloader

        Args:
            output_dir: Directory where files will be saved
            logger: Optional logger instance
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"Comenzado {self.__class__.__name__} con directorio de saída: {self.output_dir}"
        )

        self._thread_local = threading.local()

    @property
    def session(self) -> requests.Session:
        """
        Get or create a requests Session for the current thread.

        Returns:
            A requests.Session instance specific to the current thread
        """
        if not hasattr(self._thread_local, "session"):
            self._thread_local.session = requests.Session()
            self._thread_local.session.headers.update(get_headers())
        return self._thread_local.session

    @abstractmethod
    def fetch_items(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch available items from the source

        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of items with metadata
        """
        pass

    @abstractmethod
    def download_item(self, item: dict[str, Any]) -> bool:
        """
        Download a single item

        Args:
            item: Item metadata from fetch_items

        Returns:
            True if successful, False otherwise
        """
        pass

    def fetch_new(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch new items that haven't been downloaded yet

        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of new items to download
        """
        all_items = self.fetch_items(date_from, date_to)
        new_items = []

        for item in all_items:
            if not self.is_downloaded(item):
                new_items.append(item)
                self.logger.debug(f"Novo elemento atopado: {self.get_item_id(item)}")
            else:
                self.logger.debug(f"Elemento xa descargado: {self.get_item_id(item)}")

        self.logger.info(
            f"Atopáronse {len(new_items)} elementos novos de {len(all_items)} en total"
        )
        return new_items

    def download(
        self,
        items: list[dict[str, Any]] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        force: bool = False,
    ) -> dict[str, int]:
        """
        Download items in parallel using ThreadPoolExecutor.

        Args:
            items: Optional list of items to download. If None, fetches new items
            date_from: Optional start date filter (used if items is None)
            date_to: Optional end date filter (used if items is None)
            force: If True, re-download even if already exists

        Returns:
            Dictionary with download statistics
        """
        if items is None:
            items = self.fetch_items(date_from, date_to)

        stats = {"success": 0, "failed": 0, "skipped": 0}
        to_download = []
        failed_items: dict[str, dict[str, Any]] = {}

        for item in items:
            item_id = self.get_item_id(item)
            if not force and self.is_downloaded(item):
                self.logger.info(f"Saltando xa descargado: {item_id}")
                stats["skipped"] += 1
                continue
            to_download.append(item)

        self.logger.info(f"Comezando a descarga paralela con {WORKERS} threads...")

        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            while to_download:
                futures = {
                    executor.submit(self.download_item, item): item
                    for item in to_download
                }

                to_download = []
                for future in as_completed(futures):
                    item = futures[future]
                    item_id = self.get_item_id(item)
                    try:
                        success = future.result()
                        if success:
                            stats["success"] += 1
                            self.logger.info(f"Descargado correctamente: {item_id}")
                            if item_id in failed_items:
                                del failed_items[item_id]
                        else:
                            if item_id not in failed_items:
                                failed_items[item_id] = {"item": item, "attempts": 1}
                            else:
                                failed_items[item_id]["attempts"] += 1

                            if failed_items[item_id]["attempts"] <= MAX_RETRIES:
                                to_download.append(item)
                                self.logger.warning(
                                    f"Reintento {failed_items[item_id]['attempts']} de {item_id}"
                                )
                            else:
                                stats["failed"] += 1
                                self.logger.error(
                                    f"Erro na descarga despois dos reintentos: {item_id}"
                                )
                    except Exception as e:
                        if item_id not in failed_items:
                            failed_items[item_id] = {"item": item, "attempts": 1}
                        else:
                            failed_items[item_id]["attempts"] += 1

                        if failed_items[item_id]["attempts"] <= MAX_RETRIES:
                            to_download.append(item)
                            self.logger.warning(
                                f"Reintento {failed_items[item_id]['attempts']} de {item_id} por culpa do erro: {e}"
                            )
                        else:
                            stats["failed"] += 1
                            self.logger.error(
                                f"Erro na descarga {item_id} despois dos reintentos: {e}"
                            )

        self.logger.info(
            f"Descarga completada - Exitosas: {stats['success']}, "
            f"Falladas: {stats['failed']}, Omitidas: {stats['skipped']}"
        )
        return stats

    def get_downloaded_items(self) -> list[str]:
        """
        Get list of downloaded item IDs from the output directory

        Returns:
            List of item IDs
        """
        items = []
        if self.output_dir.exists():
            for item_path in self.output_dir.iterdir():
                if item_path.is_file() or item_path.is_dir():
                    items.append(item_path.name)
        return items

    def is_downloaded(self, item: dict[str, Any]) -> bool:
        """
        Check if an item has already been downloaded

        Args:
            item: Item metadata

        Returns:
            True if already downloaded
        """
        item_id = self.get_item_id(item)
        program = item.get("programa")

        # Determine base path
        base_path = self.output_dir / program if program else self.output_dir
        item_dir = base_path / item_id
        wav_path = (
            item_dir / f"{item_id}.wav" if program else base_path / f"{item_id}.wav"
        )

        # If program directory exists, check files inside
        if program and item_dir.is_dir():
            vtt_path = item_dir / f"{item_id}.vtt"
            pdf_path = next(
                (p for p in item_dir.iterdir() if p.suffix.lower() == ".txt"), None
            )
            if not (
                wav_path.exists()
                and vtt_path.exists()
                and (pdf_path or not item.get("pdf_text"))
            ):
                return False
        else:
            # If directory doesn't exist, fallback to WAV in program or root
            if program and not base_path.exists():
                return False
            if program:
                wav_path = base_path / f"{item_id}.wav"
                def_path = base_path / item_id
                if not (
                    wav_path.exists()
                    or def_path.exists()
                    or any(p.name.startswith(item_id) for p in base_path.iterdir())
                ):
                    return False
            elif not wav_path.exists():
                return False

        # Check audio duration if available
        link = item.get("link")
        expected_duration = self.get_remote_duration(link)

        if expected_duration is not None and wav_path.exists():
            duration_real = get_audio_duration(wav_path)
            if duration_real is None:
                return False
            if abs(expected_duration - duration_real) > 2:
                return False

        return True

    @abstractmethod
    def get_item_id(self, item: dict[str, Any]) -> str:
        """
        Get unique identifier for an item

        Args:
            item: Item metadata

        Returns:
            Unique identifier string
        """
        pass

    def filter_by_date(
        self,
        items: list[dict[str, Any]],
        date_from: date | None = None,
        date_to: date | None = None,
        date_field: str = "date",
    ) -> list[dict[str, Any]]:
        """
        Filter items by date range

        Args:
            items: List of items to filter
            date_from: Optional start date
            date_to: Optional end date
            date_field: Name of the date field in item dict

        Returns:
            Filtered list of items
        """
        if not date_from and not date_to:
            return items

        filtered = []
        for item in items:
            item_date = item.get(date_field)
            if not item_date:
                continue

            # Convert to date object if necessary
            if isinstance(item_date, str):
                try:
                    item_date = datetime.strptime(item_date, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        item_date = datetime.strptime(item_date, "%d/%m/%Y").date()
                    except ValueError:
                        self.logger.warning(f"Non se puido parsear a data: {item_date}")
                        continue
            elif isinstance(item_date, datetime):
                item_date = item_date.date()

            # Apply filters
            if date_from and item_date < date_from:
                continue
            if date_to and item_date > date_to:
                continue

            filtered.append(item)

        self.logger.info(
            f"Filtrados {len(items)} elemnetos a {len(filtered)} polo rango de datas"
        )
        return filtered

    class DateCheckResult(NamedTuple):
        should_skip: bool
        should_stop: bool

    def check_date_validity(
        self, parsed_date: Any, date_from: date | None, date_to: date | None
    ) -> DateCheckResult:
        """
        Determines whether to continue or stop scraping based on the parsed date.

        Args:
            parsed_date: The extracted date (may not always be a date object).
            date_from: Minimum allowed date.
            date_to: Maximum allowed date.

        Returns:
            A tuple (continue_page, stop_scraping):
                - continue_page: whether to skip this date and continue scraping.
                - stop_scraping: whether to stop scraping.
        """
        if not isinstance(parsed_date, date):
            # If it's not a valid date object, ignore date checks
            return self.DateCheckResult(False, False)

        if date_to and parsed_date > date_to:
            # Date is too recent, skip this entry
            return self.DateCheckResult(True, False)
        if date_from and parsed_date < date_from:
            # Too old, stop scraping further
            return self.DateCheckResult(False, True)

        return self.DateCheckResult(False, False)

    def get_status(self) -> dict[str, Any]:
        """
        Get status information about downloads

        Returns:
            Dictionary with status information
        """
        downloaded = self.get_downloaded_items()
        total_size = 0

        for item_name in downloaded:
            item_path = self.output_dir / item_name
            if item_path.is_file():
                total_size += item_path.stat().st_size
            elif item_path.is_dir():
                total_size += sum(
                    f.stat().st_size for f in item_path.rglob("*") if f.is_file()
                )

        return {
            "source": self.__class__.__name__,
            "output_dir": str(self.output_dir),
            "downloaded_count": len(downloaded),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def get_remote_duration(self, url: str) -> float | None:
        """
        Gets the duration of a remote audio in seconds (without downloading the entire file if possible).

        First, it tries with ffprobe to get the duration of audio/video episodes.
        If that fails, it attempts with yt-dlp.

        Args:
            url: URL of the audio or episode

        Returns:
            Duration in seconds, or None if it could not be obtained
        """
        if not url:
            return None

        # First attempt with ffprobe (faster)
        try:
            ffprobe_cmd = [
                "ffprobe",
                "-user_agent",
                DEFAULT_HEADERS["User-Agent"],
                "-referer",
                DEFAULT_HEADERS["Referer"],
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                url,
            ]
            ffprobe_res = subprocess.run(
                ffprobe_cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT
            )

            if ffprobe_res.returncode == 0 and ffprobe_res.stdout.strip():
                try:
                    duration = float(ffprobe_res.stdout.strip())
                    if duration > 0:
                        return duration
                except ValueError:
                    pass
            else:
                pass
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

        # Second attempt if ffprobe failed
        try:
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "--skip-download",
                "--print-json",
                "--no-warnings",
                url,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT
            )

            if result.returncode != 0:
                logger.warning(
                    f"yt-dlp erro ({result.returncode}) en {url}: {result.stderr.strip()}"
                )
                return None

            info = json.loads(result.stdout.strip())
            duration = info.get("duration")
            if duration and float(duration) > 0:
                return float(duration)

            # If yt-dlp doesn't show the duration, probe with the real URL
            real_url = info.get("url", url)
            if real_url and real_url != url:
                ffprobe_cmd = [
                    "ffprobe",
                    "-user_agent",
                    DEFAULT_HEADERS["User-Agent"],
                    "-referer",
                    DEFAULT_HEADERS["Referer"],
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    real_url,
                ]
                ffprobe_res = subprocess.run(
                    ffprobe_cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT
                )

                if ffprobe_res.returncode == 0 and ffprobe_res.stdout.strip():
                    try:
                        return float(ffprobe_res.stdout.strip())
                    except ValueError:
                        logger.warning(
                            f"Duración non numérica de ffprobe para {real_url}: {ffprobe_res.stdout.strip()}"
                        )
                else:
                    logger.warning(
                        f"ffprobe non puido obter duración de {real_url}: {ffprobe_res.stderr.strip()}"
                    )

        except subprocess.TimeoutExpired:
            logger.warning(f"yt-dlp esgotou o tempo de espera para {url}")
        except Exception as e:
            logger.warning(f"Erro ao usar yt-dlp para {url}: {e}")

        return None
