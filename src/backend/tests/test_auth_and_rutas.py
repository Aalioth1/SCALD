from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def test_auth_register_and_login():
    client = TestClient(app)
    email = unique_email("ana")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "email": email,
            "password": "SecurePass123!",
            "role": "AUDITOR",
        },
    )
    assert response.status_code == 201, response.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert login.status_code == 200, login.text
    data = login.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_hoja_ruta_create_and_duplicate_validation():
    client = TestClient(app)
    email = unique_email("admin")
    codigo = f"HRD-2026-{uuid4().int % 9000 + 1000}"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Admin",
            "apellido": "Sistema",
            "email": email,
            "password": "SecurePass123!",
            "role": "ADMIN",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    ).json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "codigo": codigo,
        "tipo": "HRD",
        "fecha": "2026-09-15",
        "ruta": "Ruta Norte",
        "transporte": "Transportes X",
        "cantidad_declarada": 12,
        "estado": "ACTIVA",
    }

    first = client.post("/api/v1/hojas-ruta", json=payload, headers=headers)
    assert first.status_code == 201, first.text

    duplicate = client.post("/api/v1/hojas-ruta", json=payload, headers=headers)
    assert duplicate.status_code == 409, duplicate.text


def test_pistoleo_requires_valid_bulto_and_hoja_ruta():
    client = TestClient(app)
    email = unique_email("audit")
    codigo_hoja = f"HRE-2026-{uuid4().int % 9000 + 1000}"
    codigo_bulto = f"BUL-{uuid4().int % 900000 + 100000}"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Audit",
            "apellido": "Uno",
            "email": email,
            "password": "SecurePass123!",
            "role": "AUDITOR",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": codigo_hoja,
            "tipo": "HRE",
            "fecha": "2026-09-16",
            "ruta": "Ruta Sur",
            "transporte": "Transportes Y",
            "cantidad_declarada": 3,
            "estado": "ACTIVA",
        },
        headers=headers,
    )
    assert hoja.status_code == 201, hoja.text

    bulto = client.post(
        "/api/v1/bultos",
        json={
            "codigo": codigo_bulto,
            "hoja_ruta_id": hoja.json()["id"],
            "estado": "PENDIENTE",
            "pistoleado": False,
            "fecha": "2026-09-16",
        },
        headers=headers,
    )
    assert bulto.status_code == 201, bulto.text

    pistoleo = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": codigo_bulto, "hoja_ruta_id": hoja.json()["id"]},
        headers=headers,
    )
    assert pistoleo.status_code == 201, pistoleo.text
    assert pistoleo.json()["estado"] in {"OK", "PISTOLEADO"}
