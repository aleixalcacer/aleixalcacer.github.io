"""
cvn.py — Librería para obtener el CVN-XML desde el portal público de FECYT.

Uso desde sync.py:
    from cvn import fetch_cvn_xml
    xml_bytes = fetch_cvn_xml(orcid)
"""

from __future__ import annotations

import base64
import io
import tempfile
import urllib.request
import zipfile
from pathlib import Path

FECYT_URL = "https://editor.cvn.fecyt.es/editor/cvnOnline/{orcid}"


def fetch_cvn_xml(orcid: str) -> bytes:
    """Descarga el PDF del CVN desde FECYT y extrae el CVN-XML embebido."""
    url = FECYT_URL.format(orcid=orcid)
    print(f"Descargando CVN desde '{url}'…")
    with urllib.request.urlopen(url) as response:
        pdf_bytes = response.read()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        return extract_cvn_xml(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def extract_cvn_xml(pdf_path: Path) -> bytes:
    """Extrae el CVN-XML embebido en los metadatos del PDF de FECYT."""
    import pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    meta = reader.metadata or {}
    b64 = meta.get("/CVN-XML")
    if not b64:
        raise ValueError(
            f"{pdf_path}: el PDF no contiene la clave /CVN-XML en los metadatos."
        )
    raw = base64.b64decode(b64)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = zf.namelist()
        xml_name = next((n for n in names if n.endswith(".xml")), names[0])
        return zf.read(xml_name)
