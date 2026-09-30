from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_parser_service import PdfParseError, parse_hoja_ruta_text


HRD_TEXT = """
CMK Logística
N° Definitiva HRD-2026-1638
HRD-2026-1638
Ruta Origen HR-2026-2019
Chofer NEWTRANS Auxiliar POR ASIGNAR
Vehiculo --- Fecha Generación 20/08/2026 10:14
Ruta(s) Despacho COURIER-N
22 Facturas
39 Bultos Capturados
OV Factura Cant. de Bultos Cliente Dirección Bultos
376889 800332 1 CLINICA ALEMANA OSORNO BU00077736
376861 800330 4 CLINICA ANDES SALUD CHILLAN BU00077776 BU00077745 BU00077761 BU00077770
"""

HRE_TEXT = """
HOJA DE RUTA
N° HRE-2026-0775
Fecha: 20/08/2026 06:38
Conductor: ORLANDO FREDDY VALENZUELA BAEZ
Auxiliar: RUTA PROPIA VALENZUELA BAEZ
Vehículo: POR ASIGNAR
Ruta(s): SAMEDAY RUTA-A1
TRL(s): —
OV Factura BU Cant. Cliente Dirección Comuna
376617 800123 BU00077040 BU00076780 2 CLINICA REÑACA
376715 799704 BU00076720 1 FARMACIA PROFAR
"""


def test_parser_reads_hrd_cmk_layout():
    parsed = parse_hoja_ruta_text(HRD_TEXT, "HRD-2026-1638.pdf")

    assert parsed["codigo"] == "HRD-2026-1638"
    assert parsed["tipo"] == "HRD"
    assert parsed["fecha"].isoformat() == "2026-08-20"
    assert parsed["ruta"] == "COURIER-N"
    assert parsed["transporte"] == "NEWTRANS"
    assert parsed["cantidad_declarada"] == 39
    assert parsed["bultos"] == ["BU00077736", "BU00077776", "BU00077745", "BU00077761", "BU00077770"]


def test_parser_reads_hre_reparto_layout():
    parsed = parse_hoja_ruta_text(HRE_TEXT, "HRE-2026-0775.pdf")

    assert parsed["codigo"] == "HRE-2026-0775"
    assert parsed["tipo"] == "HRE"
    assert parsed["fecha"].isoformat() == "2026-08-20"
    assert parsed["ruta"] == "SAMEDAY RUTA-A1"
    assert parsed["transporte"] == "ORLANDO FREDDY VALENZUELA BAEZ"
    assert parsed["cantidad_declarada"] == 3
    assert parsed["bultos"] == ["BU00077040", "BU00076780", "BU00076720"]


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
