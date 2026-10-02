from datetime import date, datetime, timezone
from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app
from app.services.reporte_pdf import IncidenciaPdf, _tabla_incidencias


def test_reports_reflect_route_and_pistoleo_metrics():
    client = TestClient(app)
    email = f"report-{uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Reportes",
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
    headers = {"Authorization": f"Bearer {token}"}

    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-25",
            "ruta": "Ruta Reportes",
            "cantidad_declarada": 2,
        },
        headers=headers,
    )
    bulto = client.post(
        "/api/v1/bultos",
        json={
            "codigo": f"BU{uuid4().int % 90000000 + 10000000}",
            "hoja_ruta_id": hoja.json()["id"],
        },
        headers=headers,
    )
    payload = {"codigo_bulto": bulto.json()["codigo"], "hoja_ruta_id": hoja.json()["id"]}
    client.post("/api/v1/pistoleos", json=payload, headers=headers)
    client.post("/api/v1/pistoleos", json=payload, headers=headers)

    summary = client.get("/api/v1/reportes/resumen", headers=headers)
    detail = client.get(f"/api/v1/reportes/hoja-ruta/{hoja.json()['id']}", headers=headers)

    assert summary.status_code == 200, summary.text
    assert detail.status_code == 200, detail.text
    assert detail.json()["total_bultos_esperados"] == 1
    assert detail.json()["total_pistoleos"] == 2
    assert detail.json()["ok"] == 1
    assert detail.json()["duplicados"] == 1


def test_report_filters_a_specific_day_and_downloads_pdf():
    client = TestClient(app)
    email = f"report-pdf-{uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Reporte",
            "apellido": "Diario",
            "email": email,
            "password": "SecurePass123!",
        },
    )
    assert registered.status_code == 201, registered.text
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    def crear_hoja(fecha: str):
        return client.post(
            "/api/v1/hojas-ruta",
            json={
                "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
                "tipo": "HRD",
                "fecha": fecha,
                "ruta": f"Ruta {fecha}",
                "cantidad_declarada": 1,
            },
            headers=headers,
        )

    del_dia = crear_hoja("2026-09-25")
    crear_hoja("2026-10-02")
    assert del_dia.status_code == 201, del_dia.text
    bulto = client.post(
        "/api/v1/bultos",
        json={"codigo": f"BU{uuid4().int % 90000000 + 10000000}", "hoja_ruta_id": del_dia.json()["id"]},
        headers=headers,
    )
    client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": bulto.json()["codigo"], "hoja_ruta_id": del_dia.json()["id"]},
        headers=headers,
    )

    hoy = date.today().isoformat()
    dia = client.get(f"/api/v1/reportes/resumen?fecha_desde={hoy}&fecha_hasta={hoy}", headers=headers)
    emision = client.get("/api/v1/reportes/resumen?fecha_desde=2020-01-01&fecha_hasta=2020-01-01", headers=headers)
    invalido = client.get("/api/v1/reportes/resumen?fecha_desde=2026-10-02&fecha_hasta=2026-09-01", headers=headers)
    pdf = client.get(f"/api/v1/reportes/pdf?fecha_desde={hoy}&fecha_hasta={hoy}", headers=headers)

    assert dia.status_code == 200, dia.text
    assert dia.json()["total_hojas"] == 2
    assert emision.json()["total_hojas"] == 0
    assert invalido.status_code == 400
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")
    assert f'filename="reporte-operativo-{hoy}.pdf"' in pdf.headers["content-disposition"]
    texto = "\n".join(pagina.extract_text() or "" for pagina in PdfReader(BytesIO(pdf.content)).pages)
    assert "Reporte operativo" in texto
    assert "Fecha de registro" in texto
    assert date.today().strftime("%d/%m/%Y") in texto
    if date.today().isoformat() != "2026-09-25":
        assert "25/09/2026" not in texto
    assert "Hojas de ruta" in texto
    assert "Bultos faltantes" in texto
    assert "Pistoleos fuera de OK" not in texto
    vista = client.get(f"/api/v1/reportes/operativo?fecha_desde={hoy}&fecha_hasta={hoy}", headers=headers)
    assert vista.status_code == 200, vista.text
    assert vista.json()["resumen"]["total_hojas"] == 2
    assert len(vista.json()["hojas"]) == 2
    assert vista.json()["hojas"][0]["registro"] == hoy


def test_closed_incidents_are_shown_as_regularized_in_the_report():
    html = _tabla_incidencias(
        [
            IncidenciaPdf(
                fecha=datetime.now(timezone.utc),
                hoja="HRD-2026-2512",
                bulto="BU00115725",
                tipo="DUPLICADO",
                estado="ANULADO",
                observaciones="Pistoleo eliminado",
            ),
            IncidenciaPdf(
                fecha=datetime.now(timezone.utc),
                hoja="HRD-2026-2512",
                bulto="BU00115726",
                tipo="DUPLICADO",
                estado="PENDIENTE",
                observaciones=None,
            ),
        ]
    )
    assert html.count("REGULARIZADO") == 1
    assert html.count("PENDIENTE") == 1
    assert "ANULADO" not in html


def test_foreign_bulto_observations_follow_the_resolution():
    momento = datetime.now(timezone.utc)
    html = _tabla_incidencias(
        [
            IncidenciaPdf(
                fecha=momento,
                hoja="HRD-2026-2512",
                bulto="BU00115597",
                tipo="NO PERTENECE",
                estado="REASIGNADO",
                observaciones="El bulto pertenece a otra hoja",
            ),
            IncidenciaPdf(
                fecha=momento,
                hoja="HRD-2026-2512",
                bulto="BU00115598",
                tipo="NO PERTENECE",
                estado="ANULADO",
                observaciones="El bulto pertenece a otra hoja",
            ),
        ]
    )
    assert "El bulto se cambió a esta ruta" in html
    assert "Pistoleo eliminado" in html
    assert "El bulto pertenece a otra hoja" not in html
