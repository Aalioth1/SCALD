from __future__ import annotations

import re
from datetime import date, datetime
from io import BytesIO

from pypdf import PdfReader

BU_RE = re.compile(r"BU\d{8}", re.IGNORECASE)
HR_RE = re.compile(r"HR[DE]-\d{4}-\d+", re.IGNORECASE)


class PdfParseError(ValueError):
    """Error de validación o extracción de una hoja de ruta PDF."""


def parse_pdf_bytes(content: bytes, filename: str) -> dict:
    try:
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise PdfParseError("El PDF no pudo ser leído") from exc

    return parse_hoja_ruta_text(text, filename)


def parse_hoja_ruta_text(text: str, filename: str = "") -> dict:
    normalized = text or ""
    code_match = HR_RE.search(normalized)
    if code_match is None:
        code_match = HR_RE.search(filename)
    if code_match is None:
        raise PdfParseError("No se encontró un código HRD/HRE")

    codigo = code_match.group(0).upper()
    tipo = codigo[:3]
    bultos = list(dict.fromkeys(match.upper() for match in BU_RE.findall(normalized)))
    if not bultos:
        raise PdfParseError("No se encontraron códigos de bulto BU########")

    fecha = _extract_date(normalized, tipo) or date.today()
    ruta = _extract_route(normalized, tipo) or "SIN INFORMACION"
    transporte = _extract_transport(normalized, tipo) or None
    declared = _extract_declared_count(normalized, tipo)

    return {
        "codigo": codigo,
        "tipo": tipo,
        "fecha": fecha,
        "ruta": ruta[:200],
        "transporte": transporte[:200] if transporte else None,
        "cantidad_declarada": declared if declared is not None else len(bultos),
        "bultos": bultos,
        "bultos_declarados": declared,
        "archivo": filename,
    }


def _extract_date(text: str, tipo: str) -> date | None:
    patterns = [
        r"Fecha\s+Generaci[oó]n\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
        r"Generado\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
        r"Fecha\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d/%m/%Y").date()
            except ValueError:
                return None
    return None


def _extract_route(text: str, tipo: str) -> str | None:
    match = re.search(
        r"Ruta\(s\)(?:\s*Despacho)?\s*:?\s*(.+?)(?=\s*TRL|\s*OV\s+Factura)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip(" -")


def _extract_transport(text: str, tipo: str) -> str | None:
    match = re.search(
        r"(?:Chofer|Conductor)\s*:?\s*(.+?)\s*(?:Auxiliar|Veh[ií]culo)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip(" -")


def _extract_declared_count(text: str, tipo: str) -> int | None:
    patterns = [
        r"Total\s+Bultos\s*\(QB\)\s*:?\s*(\d+)",
        r"(\d+)\s*Bultos\s+Capturados",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None
