from __future__ import annotations

import feedparser
from dataclasses import dataclass
from pathlib import Path
from typing import List
import requests
from bs4 import BeautifulSoup
import logging

from src.common.io import write_json

log = logging.getLogger(__name__)

@dataclass
class CTIItem:
    title: str
    link: str
    published: str
    text: str

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
    except ImportError:
        log.warning("PyPDF2 not installed. Skipping PDF: %s", pdf_path)
        return ""
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n\n".join(text_parts)
    except Exception as e:
        log.warning("Failed to extract from PDF %s: %s", pdf_path, e)
        return ""

def ingest_pdfs(pdf_dir: Path) -> List[CTIItem]:
    """Ingest CTI reports from PDF files."""
    items: List[CTIItem] = []
    
    if not pdf_dir.exists():
        log.warning("PDF directory not found: %s", pdf_dir)
        return items
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    log.info("Found %d PDF files in %s", len(pdf_files), pdf_dir)
    
    for pdf_file in pdf_files:
        text = extract_pdf_text(pdf_file)
        if text and len(text) > 100:  # Valid extraction
            items.append(CTIItem(
                title=pdf_file.stem,
                link=str(pdf_file),
                published="",
                text=text
            ))
            log.info("Extracted %d chars from: %s", len(text), pdf_file.name)
        else:
            log.warning("No/little text extracted from: %s", pdf_file.name)
    
    return items

def fetch_text(url: str, timeout: int = 20, max_bytes: int = 2_000_000) -> str:
    """Fetch a URL and extract visible text. Best-effort for CTI pages."""
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    content = r.content[:max_bytes]
    # decode best-effort
    try:
        html = content.decode(r.encoding or "utf-8", errors="ignore")
    except Exception:
        html = content.decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def ingest_sources(sources: List[str], per_source_limit: int = 10, timeout: int = 20, max_bytes: int = 2_000_000) -> List[CTIItem]:
    """Ingest CTI from a mixed list of RSS feed URLs and normal web pages.

    - If the source parses as a feed and has entries: fetch each entry page (best effort).
    - If it has no entries: treat the source itself as a single CTI page and scrape text.
    """
    items: List[CTIItem] = []
    for url in sources:
        try:
            feed = feedparser.parse(url)
        except Exception:
            feed = None

        entries = []
        if feed and getattr(feed, "entries", None):
            entries = list(feed.entries)[:per_source_limit]

        if entries:
            for e in entries:
                link = getattr(e, "link", "") or url
                title = getattr(e, "title", "") or link
                published = getattr(e, "published", "") or ""
                text = ""
                try:
                    text = fetch_text(link, timeout=timeout, max_bytes=max_bytes)
                except Exception:
                    # fallback to summary if available
                    text = getattr(e, "summary", "") or getattr(e, "description", "") or ""
                items.append(CTIItem(title=title, link=link, published=published, text=text))
        else:
            # Not a feed (or empty feed). Treat as a normal CTI page.
            try:
                text = fetch_text(url, timeout=timeout, max_bytes=max_bytes)
            except Exception:
                continue
            items.append(CTIItem(title=url, link=url, published="", text=text))
    return items

def save_items(out_dir: Path, items: List[CTIItem]) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for i, it in enumerate(items):
        p = out_dir / f"cti_{i:03d}.json"
        write_json(p, {"title": it.title, "link": it.link, "published": it.published, "text": it.text})
        paths.append(p)
    return paths
