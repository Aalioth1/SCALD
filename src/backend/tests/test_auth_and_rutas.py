from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def authenticated_client(client: TestClient) -> dict[str, str]:
    email = unique_email("audit")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Audit",
            "apellido": "Prueba",
            "email": email,
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201, response.text
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


def test_public_register_cannot_assign_admin_role():
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Intento",
            "apellido": "Admin",
            "email": unique_email("privilege"),
            "password": "SecurePass123!",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["role"] == "AUDITOR"


def test_hoja_ruta_create_and_duplicate_validation():
    client = TestClient(app)
    codigo = f"HRD-2026-{uuid4().int % 9000 + 1000}"

    token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin-fixture@example.com", "password": "SecurePass123!"},
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


def test_second_pistoleo_is_duplicate():
    client = TestClient(app)
    headers = authenticated_client(client)
    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-20",
            "ruta": "Ruta Duplicados",
            "cantidad_declarada": 1,
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

    first = client.post("/api/v1/pistoleos", json=payload, headers=headers)
    second = client.post("/api/v1/pistoleos", json=payload, headers=headers)

    assert first.json()["estado"] == "OK"
    assert second.json()["estado"] == "DUPLICADO"


def test_unknown_bulto_is_without_expected_list():
    client = TestClient(app)
    headers = authenticated_client(client)
    response = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": f"BU{uuid4().int % 90000000 + 10000000}"},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["estado"] == "SIN LISTA ESPERADA"


def test_bulto_from_another_route_is_not_assigned_to_scan_route():
    client = TestClient(app)
    headers = authenticated_client(client)
    origen = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRE-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRE",
            "fecha": "2026-09-21",
            "ruta": "Ruta Origen",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    destino = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRE-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRE",
            "fecha": "2026-09-21",
            "ruta": "Ruta Destino",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    bulto = client.post(
        "/api/v1/bultos",
        json={
            "codigo": f"BU{uuid4().int % 90000000 + 10000000}",
            "hoja_ruta_id": origen.json()["id"],
        },
        headers=headers,
    )

    response = client.post(
        "/api/v1/pistoleos",
        json={
            "codigo_bulto": bulto.json()["codigo"],
            "hoja_ruta_id": destino.json()["id"],
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["estado"] == "NO PERTENECE"


def test_duplicate_incidence_can_be_regularized_once():
    client = TestClient(app)
    headers = authenticated_client(client)
    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-22",
            "ruta": "Ruta Incidencias",
            "cantidad_declarada": 1,
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

    pending = client.get("/api/v1/incidencias?estado=PENDIENTE", headers=headers)
    assert pending.status_code == 200, pending.text
    incidence = next(item for item in pending.json() if item["tipo"] == "DUPLICADO")

    resolved = client.patch(
        f"/api/v1/incidencias/{incidence['id']}/regularizar",
        json={"observaciones": "Validado con el transportista"},
        headers=headers,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["estado"] == "REGULARIZADO"

    repeated = client.patch(
        f"/api/v1/incidencias/{incidence['id']}/anular",
        json={},
        headers=headers,
    )
    assert repeated.status_code == 409, repeated.text


def test_reassignment_moves_bulto_and_closes_incidence():
    client = TestClient(app)
    headers = authenticated_client(client)
    origin = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-23",
            "ruta": "Ruta Origen Reasignacion",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    destination = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-23",
            "ruta": "Ruta Destino Reasignacion",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    bulto = client.post(
        "/api/v1/bultos",
        json={
            "codigo": f"BU{uuid4().int % 90000000 + 10000000}",
            "hoja_ruta_id": origin.json()["id"],
        },
        headers=headers,
    )

    response = client.post(
        "/api/v1/reasignaciones",
        json={
            "bulto_id": bulto.json()["id"],
            "hoja_destino_id": destination.json()["id"],
            "motivo": "Regularización informada por transporte",
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["hoja_origen_id"] == origin.json()["id"]
    assert response.json()["hoja_destino_id"] == destination.json()["id"]

    moved = client.get(f"/api/v1/bultos/{bulto.json()['id']}", headers=headers)
    assert moved.status_code == 200, moved.text
    assert moved.json()["hoja_ruta_id"] == destination.json()["id"]
    assert moved.json()["estado"] == "REASIGNADO"

    reassigned = client.get("/api/v1/incidencias?estado=REASIGNADO", headers=headers)
    assert reassigned.status_code == 200, reassigned.text
    assert any(item["bulto_id"] == bulto.json()["id"] for item in reassigned.json())


def test_reassignment_rejects_same_origin_and_destination():
    client = TestClient(app)
    headers = authenticated_client(client)
    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRE-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRE",
            "fecha": "2026-09-24",
            "ruta": "Ruta Igual",
            "cantidad_declarada": 1,
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

    response = client.post(
        "/api/v1/reasignaciones",
        json={
            "bulto_id": bulto.json()["id"],
            "hoja_destino_id": hoja.json()["id"],
            "motivo": "Prueba inválida",
        },
        headers=headers,
    )

    assert response.status_code == 409, response.text
