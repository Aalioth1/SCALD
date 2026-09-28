from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


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
