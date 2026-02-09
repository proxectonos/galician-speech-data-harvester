"""
PDF processing utilities
"""

import logging
import re
from pathlib import Path

import pypdf

logger = logging.getLogger(__name__)


def pdf_to_text(pdf_file: Path, output_file: Path | None = None) -> str | None:
    """
    Extract text from PDF file

    Args:
        pdf_file: Path to PDF file
        output_file: Optional path to save extracted text

    Returns:
        Extracted text string, or None if error
    """
    try:
        text = ""

        with open(pdf_file, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            logger.info(f"Procesando PDF con {num_pages} páxinas: {pdf_file}")

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()

                if page_text:
                    text += page_text
                    # Add page separator for clarity
                    text += f"\n\n--- Páxina {page_num + 1} ---\n\n"

        # Clean up text
        text = clean_pdf_text(text)

        # Save to file if requested
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

        return text

    except Exception:
        return None


def clean_pdf_text(text: str) -> str:
    """
    Clean extracted PDF text

    Args:
        text: Raw text from PDF

    Returns:
        Cleaned text
    """
    # Remove page markers added by our extraction
    text = re.sub(r"^--- Páxina \d+ ---\s*$", "", text, flags=re.MULTILINE)

    # Remove repeated headers (Parliament documents)
    # Pattern: "XII lexislatura. Serie Pleno. Número XX. DD de mes de AAAA DIARIO DE SESIÓNS DO PARLAMENTO DE GALICIA"
    text = re.sub(
        r"^[IVX]+ lexislatura\. Serie \w+\. Número \d+\. .+ DIARIO DE SESIÓNS DO PARLAMENTO DE GALICIA\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Remove CSV verification blocks (3 lines: CSV, Verificación, URL)
    text = re.sub(
        r"^CSV: [A-Za-z0-9\-]+\s*\n"
        r"Verificación:\s*\n"
        r"https://sede\.parlamentodegalicia\.gal/tramites/csv/\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Remove standalone page numbers at the end of lines (Páx. XX)
    text = re.sub(r"\(Páx\. \d+\.\)", "", text)

    # Remove multiple consecutive spaces
    text = re.sub(r" +", " ", text)

    # Remove multiple consecutive newlines (keep max 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix broken words at line endings (common in PDFs)
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Remove page numbers that appear alone on lines
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)

    # Remove lines with only dots or underscores (often used as separators)
    text = re.sub(r"^[\._\s]+$", "", text, flags=re.MULTILINE)

    # Clean up excessive whitespace again after all removals
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim whitespace
    text = text.strip()

    return text


def extract_pdf_metadata(pdf_file: Path) -> dict:
    """
    Extract metadata from PDF file

    Args:
        pdf_file: Path to PDF file

    Returns:
        Dictionary with metadata
    """
    metadata = {}

    try:
        with open(pdf_file, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)

            # Get document info
            if pdf_reader.metadata:
                info = pdf_reader.metadata

                # Extract common fields
                metadata["title"] = info.get("/Title", "")
                metadata["author"] = info.get("/Author", "")
                metadata["subject"] = info.get("/Subject", "")
                metadata["creator"] = info.get("/Creator", "")
                metadata["producer"] = info.get("/Producer", "")

                # Handle dates
                if "/CreationDate" in info:
                    metadata["creation_date"] = str(info["/CreationDate"])
                if "/ModDate" in info:
                    metadata["modification_date"] = str(info["/ModDate"])

            # Add page count
            metadata["pages"] = len(pdf_reader.pages)

    except Exception as e:
        logger.error(f"Erro extraendo metadata de {pdf_file}: {str(e)}")

    return metadata


def search_text_in_pdf(
    pdf_file: Path, search_term: str, case_sensitive: bool = False
) -> list:
    """
    Search for text in PDF and return matches with page numbers

    Args:
        pdf_file: Path to PDF file
        search_term: Text to search for
        case_sensitive: Whether search is case sensitive

    Returns:
        List of tuples (page_number, context)
    """
    matches = []

    try:
        with open(pdf_file, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)

            # Prepare search term
            if not case_sensitive:
                search_term = search_term.lower()

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                if not case_sensitive:
                    search_text = text.lower()
                else:
                    search_text = text

                if search_term in search_text:
                    # Find context around match
                    lines = text.split("\n")
                    for line in lines:
                        check_line = line.lower() if not case_sensitive else line
                        if search_term in check_line:
                            matches.append((page_num + 1, line.strip()))

    except Exception as e:
        logger.error(f"Erro buscando en PDF {pdf_file}: {str(e)}")

    return matches


def merge_pdf_texts(pdf_files: list, output_file: Path) -> bool:
    """
    Merge text from multiple PDFs into a single text file

    Args:
        pdf_files: List of PDF file paths
        output_file: Path to output text file

    Returns:
        True if successful, False otherwise
    """
    try:
        all_text = []

        for pdf_file in pdf_files:
            pdf_path = Path(pdf_file)
            if not pdf_path.exists():
                continue

            text = pdf_to_text(pdf_path)
            if text:
                all_text.append(f"\n\n{'=' * 60}\n")
                all_text.append(f"FICHEIRO: {pdf_path.name}\n")
                all_text.append(f"{'=' * 60}\n\n")
                all_text.append(text)

        if all_text:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("".join(all_text))
            return True
        else:
            return False

    except Exception:
        return False
