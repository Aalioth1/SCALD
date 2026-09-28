from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_parser_service import PdfParseError, parse_hoja_ruta_text


def test_parser_extracts_cmk_metadata_and_bultos():
    parsed = parse_hoja_ruta_text(
        "HOJA DE RUTA HRD-2026-1638\n"
        "Fecha Generación: 28/09/2026\n"
        "Ruta(s): Norte TRL\n"
        "Conductor: Transportes X Auxiliar\n"
        "BU12345678 BU87654321\n"
    )

    assert parsed["codigo"] == "HRD-2026-1638"
    assert parsed["tipo"] == "HRD"
    assert parsed["fecha"].isoformat() == "2026-09-28"
    assert parsed["bultos"] == ["BU12345678", "BU87654321"]


def test_parser_rejects_pdf_without_expected_bultos():
    try:
        parse_hoja_ruta_text("HOJA DE RUTA HRE-2026-0775\nFecha: 28/09/2026")
    except PdfParseError as exc:
        assert "bulto" in str(exc).lower()
    else:
        raise AssertionError("El parser debería rechazar un documento sin códigos BU")


def test_import_endpoint_returns_partial_error_for_invalid_pdf():
    client = TestClient(app)
    email = f"import-{uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Importador",
            "apellido": "Prueba",
            "email": email,
            "password": "SecurePass123!",
        },
    )
    assert registered.status_code == 201, registered.text
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    ).json()["access_token"]

    response = client.post(
        "/api/v1/importaciones/hojas-ruta",
        headers={"Authorization": f"Bearer {token}"},
        files=[("archivos", ("invalido.pdf", b"no es un pdf", "application/pdf"))],
    )

    assert response.status_code == 200, response.text
    assert response.json()["archivos_fallidos"] == 1
    assert response.json()["resultados"][0]["exitoso"] is False
