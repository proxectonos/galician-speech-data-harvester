"""
Parlamento de Galicia downloader
Handles all types of parliamentary sessions:
- Pleno: DSPG_[Nº]_[DDMMAAAA].wav
- Comisión: CPG_[Nº]_[DDMMAAAA].wav
- Comisión non permanente: CPG_NP_[DDMMAAAA].wav
- Comisión especial non permanente: CPG_ENP_[DDMMAAAA].wav
- Comisión permanente non lexislativa: CPG_PNL_[DDMMAAAA].wav
- Outros: PG_[SIGLAS]_[DDMMAAAA].wav
"""

import logging
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import requests
import scrapy
import scrapydo

from src.utils.audio import convert_to_wav, get_audio_duration
from src.utils.pdf import pdf_to_text

from ..BaseDownloader import BaseDownloader
from ..config import (
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    CHUNK_SIZE,
    DEFAULT_TIMEOUT,
    DOWNLOADS_DIR,
    PARLAMENTO_CONFIG,
)

logger = logging.getLogger(__name__)


class VideosScrapySpider(scrapy.Spider):
    name = "parlamento_spider"

    def __init__(self, date_from=None, date_to=None, output_list=None):
        super().__init__()
        self.output_list = output_list if output_list is not None else []
        self.date_from = date_from
        self.date_to = date_to
        self.visited_videos = set()
        self.headers = PARLAMENTO_CONFIG["headers"]

    async def start(self):
        url_videos = f"{PARLAMENTO_CONFIG['search_url']}?view_type=list&date_from={self.date_from.strftime('%d/%m/%Y')}&date_to={self.date_to.strftime('%d/%m/%Y')}&page=1"
        yield scrapy.Request(
            url=url_videos,
            callback=self.parse_videos,
            headers=self.headers,
            meta={"pagina": 1},
        )

    # Videos
    def parse_videos(self, response):
        """
        Parse a listing page from the Parlamento site to extract video entries
        and follow links to each individual video page.

        Args:
            response: HTTP response object obtained from the request

        Returns:
            Generator of Scrapy Request objects for:
            - Each individual video page (to parse details)
            - The next listing page (to continue pagination)
        """
        pagina = response.meta["pagina"]

        programas = response.css("a.h2 ")
        logger.info(f"Páxina {pagina} atopados {len(programas)}")

        # If no videos in this page, finish the scrape
        if not programas:
            logger.info(
                f"Non se atoparon vídeos na páxina {pagina}. Rematando paxinación."
            )
            return

        for pro in programas:
            titulo = pro.css("span::text").get().strip()
            url_video = pro.attrib["href"]
            url_video = response.urljoin(url_video)
            if url_video in self.visited_videos:
                continue
            self.visited_videos.add(url_video)
            yield scrapy.Request(
                url=url_video,
                callback=self.parse_video_page_soup,
                headers=self.headers,
                meta={"title": titulo},
            )

        # Next page
        next_page_url = f"{PARLAMENTO_CONFIG['search_url']}?view_type=list&date_from={self.date_from.strftime('%d/%m/%Y')}&date_to={self.date_to.strftime('%d/%m/%Y')}&page={pagina+1}"
        yield scrapy.Request(
            url=next_page_url,
            callback=self.parse_videos,
            headers=self.headers,
            meta={"pagina": pagina + 1},
        )

    def parse_video_page_soup(self, response):
        """
        Parse videos from the Parlamento site, extract their date, and find MP4/VTT URLs.

        Args:
            response: HTTP response object obtained from the request

        Returns:
            List of dictionaries, each containing:
            - "title": Title of the video
            - "page_url": URL to the video page
            - "mp4_url": Direct MP4 URL if found
            - "vtt_url": Direct VTT (subtitle) URL if found
            - "date": Date of the video (if available)
        """
        titulo = response.meta["title"]

        date_td = response.css(
            'td[style="vertical-align:top;padding-top: 10px;"]::text'
        ).get()
        fecha_video = date_td.strip() if date_td else None

        scripts = response.css("script::text").getall()
        mp4_url, vtt_url = None, None
        for script in scripts:
            if script:
                mp4_match = re.search(r"media_url\s*=\s*'([^']+\.mp4)'", script)
                vtt_match = re.search(r"webvtt_url\s*=\s*'([^']+\.vtt[^']*)'", script)
                if mp4_match:
                    mp4_url = mp4_match.group(1)
                if vtt_match:
                    vtt_url = vtt_match.group(1)
                if mp4_url and vtt_url:
                    break

        self.output_list.append(
            {
                "title": titulo,
                "page_url": response.url,
                "mp4_url": mp4_url,
                "vtt_url": vtt_url,
                "date": fecha_video,
            }
        )


class BoletinsScrapySpider(scrapy.Spider):
    name = "boletins_spider"

    def __init__(self, date_from=None, date_to=None, output_list=None):
        super().__init__()
        self.output_list = output_list if output_list is not None else []
        self.date_from = date_from
        self.date_to = date_to
        self.headers = PARLAMENTO_CONFIG["headers"]
        self.base_url = PARLAMENTO_CONFIG["base_url"]

    async def start(self):
        url = f"{self.base_url}?paxina=1&txtBusca=&dataDesde={self.date_from}&dataAta={self.date_to}&lista=32"
        yield scrapy.Request(
            url, callback=self.parse_boletins, headers=self.headers, meta={"pagina": 1}
        )

    def parse_boletins(self, response):
        pagina = response.meta["pagina"]
        enlaces = response.css("a.text-primary-darker")
        boletins_encontrados = [
            e for e in enlaces if e.attrib.get("href", "").lower().endswith(".pdf")
        ]

        if not boletins_encontrados:
            return

        for b in boletins_encontrados:
            titulo = b.css("::text").get().strip()
            url_pdf = response.urljoin(b.attrib["href"])
            self.output_list.append({"titulo": titulo, "url_pdf": url_pdf})

        next_page = pagina + 1
        next_url = f"{self.base_url}?paxina={next_page}&txtBusca=&dataDesde={self.date_from}&dataAta={self.date_to}&lista=32"
        yield scrapy.Request(
            next_url,
            callback=self.parse_boletins,
            headers=self.headers,
            meta={"pagina": next_page},
        )


class ParlamentoDownloader(BaseDownloader):
    """Downloader for Parlamento de Galicia media and documents"""

    MESES = {
        "Xaneiro": "01",
        "Febreiro": "02",
        "Marzo": "03",
        "Abril": "04",
        "Maio": "05",
        "Xuño": "06",
        "Xullo": "07",
        "Agosto": "08",
        "Setembro": "09",
        "Outubro": "10",
        "Novembro": "11",
        "Decembro": "12",
    }
    MESES_LOWER = {k.lower(): v for k, v in MESES.items()}

    def __init__(self, output_dir: str | None = None):
        if output_dir is None:
            output_dir = str(DOWNLOADS_DIR / "parlamento")
        super().__init__(output_dir)
        self.base_url = PARLAMENTO_CONFIG["base_url"]
        self.session_types = PARLAMENTO_CONFIG["session_types"]
        self.limit_date = PARLAMENTO_CONFIG["limit_date"]
        self.headers = PARLAMENTO_CONFIG["headers"]
        scrapydo.setup()

    def parse_fecha_gallego(self, texto: str, formato: str = "ddmmaaaa") -> str:
        """
        Extracts and formats a date from a text in Galician.

        Args:
            text: Text containing the date in the format 'DD de Month de YYYY'
            format: 'ddmmaaaa' → 'DDMMYYYY', 'dd/mm/aaaa' → 'DD/MM/YYYY'

        Returns:
            Formatted date as a string, or the current date if none is found
        """
        if not texto:
            today = date.today()
            return (
                today.strftime("%d%m%Y")
                if formato == "ddmmaaaa"
                else today.strftime("%d/%m/%Y")
            )

        # Normalize spaces
        texto = re.sub(r"\s+", " ", texto.strip())

        # Extract day, month, and year
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", texto, re.IGNORECASE
        )
        if not match:
            today = date.today()
            return (
                today.strftime("%d%m%Y")
                if formato == "ddmmaaaa"
                else today.strftime("%d/%m/%Y")
            )

        dia, mes_texto, ano = match.groups()
        mes_num = self.MESES_LOWER.get(mes_texto.lower(), "01")

        if formato == "ddmmaaaa":
            return f"{int(dia):02d}{mes_num}{ano}"
        elif formato == "dd/mm/aaaa":
            return f"{int(dia):02d}/{mes_num}/{ano}"
        else:
            return f"{int(dia):02d}{mes_num}{ano}"

    def extract_tipo(self, titulo: str, numero_pdf: str | None = None) -> str:
        """Determine session type based on title and PDF number."""
        if numero_pdf or re.search(r"\bpleno\b", titulo, re.IGNORECASE):
            return "pleno"
        if re.search(
            r"comisi[oó]n\s+(?=.*especial)(?=.*NP|non\s+permanente)",
            titulo,
            re.IGNORECASE,
        ):
            return "comision_enp"
        if re.search(r"comisi[oó]n\s+(NP|non\s+permanente)", titulo, re.IGNORECASE):
            return "comision_np"
        if re.search(
            r"comisi[oó]n\s+permanente\s+non\s+lexislativa", titulo, re.IGNORECASE
        ):
            return "comision_pnl"
        if re.search(r"\bcomisi[oó]n\b", titulo, re.IGNORECASE):
            return "comision"
        return "outros"

    def generar_filename(
        self, titulo: str, fecha: str | None, numero_pdf: str | None = None
    ) -> str:
        """
        Generates the filename for a video or PDF.
        - Prefixes according to self.session_types.
        - Full sessions use PDF number if available.
        - Committees and others try to extract number or initials.
        """

        fecha_str = self.parse_fecha_gallego(fecha)

        # Detect types
        tipo = self.extract_tipo(titulo, numero_pdf)

        prefijo = self.session_types.get(tipo, "PG")

        # If there is a PDF number (only for full sessions), use it
        if numero_pdf and tipo == "pleno":
            return f"{prefijo}_{numero_pdf}_{fecha_str}"

        # Try to extract a number from the title
        numero = None
        if tipo in ["pleno", "comision"]:
            match = re.search(r"(\d+)", titulo)
            if match:
                numero = match.group(1)

        if numero:
            return f"{prefijo}_{numero}_{fecha_str}"

        # For other types without a number, generate initials
        if tipo == "outros":
            palabras = re.findall(r"\b[A-ZÁÉÍÓÚÑa-záéíóúñ]{3,}\b", titulo)
            if palabras:
                siglas = "".join(p[0].upper() for p in palabras)
                return f"{prefijo}_{siglas}_{fecha_str}"
            else:
                # Fallback: only use date
                return f"{prefijo}_{fecha_str}"

        # Pleno or Comision without number
        return f"{prefijo}_{fecha_str}"

    def procesar_boletins(self, boletins_info: list[dict[str, Any]]) -> dict[str, str]:
        """
        Processes the sesion pdfs: downloads PDFs, converts them to text, and extracts dates.

        Args:
            boletins_info: List of dictionaries with 'titulo' and 'pdf_url'

        Returns:
        Dict mapping formatted_date ('dd/mm/yyyy') -> path to the .txt file
        """
        textos_dir = Path(self.output_dir) / "textos_boletins"
        textos_dir.mkdir(parents=True, exist_ok=True)

        boletins_por_fecha = {}

        for b in boletins_info:
            titulo = b["titulo"]
            url_pdf = b["url_pdf"]
            safe_title = re.sub(r"[^\w\d]+", "_", titulo)[:50]
            output_file = textos_dir / f"{safe_title}.txt"

            if not output_file.exists():
                try:
                    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
                        r = requests.get(
                            url_pdf, headers=self.headers, timeout=DEFAULT_TIMEOUT
                        )
                        r.raise_for_status()
                        tmp_pdf.write(r.content)
                        tmp_pdf.flush()
                        pdf_to_text(Path(tmp_pdf.name), output_file=output_file)
                    logger.info(f"Boletín descargado e procesado: {titulo}")
                except Exception as e:
                    logger.error(f"Erro procesando PDF {url_pdf}: {e}")
                    continue
            else:
                logger.info(f"Boletín xa descargado e procesado: {titulo}")

            if output_file.exists():
                with open(output_file, encoding="utf-8") as f:
                    contenido = f.read()
                fecha_pdf = self.parse_fecha_gallego(contenido, formato="dd/mm/aaaa")
                boletins_por_fecha[fecha_pdf] = str(output_file)

        return boletins_por_fecha

    def fetch_items(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch parliamentary sessions from the mediateca

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            List of session items
        """
        items: list[dict[str, Any]] = []
        date_from = date_from or self.limit_date
        date_to = date_to or date.today()

        # Scraping pdfs with Scrapy
        boletins_info: list[dict[str, Any]] = []
        scrapydo.run_spider(
            BoletinsScrapySpider,
            date_from=date_from.strftime("%d/%m/%Y"),
            date_to=date_to.strftime("%d/%m/%Y"),
            output_list=boletins_info,
        )

        # Process PDFs (extract text and dates)
        boletins_por_fecha = self.procesar_boletins(boletins_info)

        # Scraping videos with Scrapy
        scrapydo.run_spider(
            VideosScrapySpider,
            date_from=date_from,
            date_to=date_to,
            output_list=items,
        )

        videos = [i for i in items if "mp4_url" in i]

        # Match PDFs with videos
        for v in videos:
            fecha = v.get("date")
            if fecha:
                fecha_formateada = self.parse_fecha_gallego(fecha, formato="dd/mm/aaaa")
                v["pdf_text"] = boletins_por_fecha.get(fecha_formateada)
            else:
                v["pdf_text"] = None

            numero_pdf = None
            if v.get("pdf_text"):
                # If pdf_text exists, try to extract the number from the PDF filename
                match = re.search(r"_([0-9]+)\.txt$", Path(v["pdf_text"]).name)
                if match:
                    numero_pdf = match.group(1)

            v["programa"] = self.extract_tipo(v["title"], numero_pdf)
            # Generate final title using generar_filename
            v["id"] = self.generar_filename(
                v.get("title", ""), v.get("date"), numero_pdf
            )

        return videos

    def download_item(self, item: dict[str, Any]) -> bool:
        """
        Download a parliamentary session with all associated files

        Args:
            item: Session metadata

        Returns:
            True if successful
        """
        # Create folder for session
        try:
            session_dir = Path(self.output_dir) / item["programa"] / item["id"]
            session_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(
                f"Erro ao crear o directorio da sesión {item.get('id', 'descoñecida')}: {e}"
            )
            return False

        # Convert to wav
        if item.get("mp4_url"):
            try:
                wav_path = session_dir / f"{item['id']}.wav"
                expected_duration = self.get_remote_duration(item["mp4_url"])
                duration_real = get_audio_duration(wav_path) if wav_path.exists() else 0
                if not wav_path.exists() or abs(expected_duration - duration_real) > 2:
                    logger.info(f"Convertendo a WAV dende: {item['mp4_url']}")
                    success = convert_to_wav(
                        item["mp4_url"], wav_path, AUDIO_SAMPLE_RATE, AUDIO_CHANNELS
                    )
                    if not success:
                        logger.error(f"Erro ao converter a WAV: {item['mp4_url']}")
                        return False
            except Exception as e:
                logger.error(
                    f"Erro ao converter a WAV para a sesión {item.get('id', 'descoñecida')}: {e}"
                )
                return False

        # Download transcription
        if item.get("vtt_url"):
            try:
                vtt_path = session_dir / f"{item['id']}.vtt"
                logger.info(f"Descargando transcrición: {vtt_path}")
                with requests.get(
                    item["vtt_url"],
                    headers=self.headers,
                    stream=True,
                    timeout=DEFAULT_TIMEOUT,
                ) as r:
                    r.raise_for_status()
                    with open(vtt_path, "wb") as f:
                        for chunk in r.iter_content(CHUNK_SIZE):
                            f.write(chunk)
            except Exception as e:
                logger.error(
                    f"Erro ao descargar a transcrición {item.get('id', 'descoñecida')}: {e}"
                )
                return False

            except requests.Timeout as e:
                logger.error(
                    f"Agotouse o tempo da descarga da transcrición {item.get('id', 'descoñecida')}: {e}"
                )

        # Copy the boletins .txt file
        if item.get("pdf_text"):
            try:
                pdf_src = Path(item["pdf_text"])
                if pdf_src.exists():
                    dest_path = session_dir / pdf_src.name
                    if not dest_path.exists():
                        shutil.copy(pdf_src, dest_path)
                        logger.info(f"Boletín copiado a {dest_path}")
            except Exception as e:
                logger.error(
                    f"Erro ao copiar o boletín para a sesión {item.get('id', 'descoñecida')}: {e}"
                )
                return False

        logger.info(f"Sesión gardada correctamente en: {session_dir}")
        return True

    def get_item_id(self, item: dict[str, Any]) -> str:
        return item.get("id")
