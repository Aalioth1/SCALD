from datetime import date
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
    assert first.json()["fecha"] == "2026-09-15"
    assert first.json()["fecha_registro"] == date.today().isoformat()

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


def test_hoja_se_cierra_cuando_todos_los_bultos_estan_pistoleados():
    client = TestClient(app)
    headers = authenticated_client(client)
    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-20",
            "ruta": "Ruta Completa",
            "cantidad_declarada": 2,
        },
        headers=headers,
    )
    assert hoja.status_code == 201, hoja.text
    codigos = [f"BU{uuid4().int % 90000000 + 10000000}" for _ in range(2)]
    for codigo in codigos:
        creado = client.post(
            "/api/v1/bultos",
            json={"codigo": codigo, "hoja_ruta_id": hoja.json()["id"]},
            headers=headers,
        )
        assert creado.status_code == 201, creado.text

    primero = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": codigos[0], "hoja_ruta_id": hoja.json()["id"]},
        headers=headers,
    )
    assert primero.status_code == 201, primero.text
    abierta = client.get(f"/api/v1/hojas-ruta/{hoja.json()['id']}", headers=headers)
    assert abierta.json()["estado"] == "ACTIVA"

    segundo = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": codigos[1], "hoja_ruta_id": hoja.json()["id"]},
        headers=headers,
    )
    assert segundo.status_code == 201, segundo.text
    cerrada = client.get(f"/api/v1/hojas-ruta/{hoja.json()['id']}", headers=headers)
    assert cerrada.json()["estado"] == "CERRADA"
    pistoleos = client.get("/api/v1/pistoleos", headers=headers)
    assert pistoleos.status_code == 200, pistoleos.text
    registrados = {item["codigo_bulto"] for item in pistoleos.json()}
    assert set(codigos) <= registrados


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


def test_auditoria_includes_bulto_and_hoja_codes():
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin-fixture@example.com", "password": "SecurePass123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    codigo_hoja = f"HRD-2026-{uuid4().int % 9000 + 1000}"
    codigo_bulto = f"BU{uuid4().int % 90000000 + 10000000}"
    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": codigo_hoja,
            "tipo": "HRD",
            "fecha": "2026-09-26",
            "ruta": "Ruta Auditoria",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    bulto = client.post(
        "/api/v1/bultos",
        json={"codigo": codigo_bulto, "hoja_ruta_id": hoja.json()["id"]},
        headers=headers,
    )
    payload = {"codigo_bulto": bulto.json()["codigo"], "hoja_ruta_id": hoja.json()["id"]}
    client.post("/api/v1/pistoleos", json=payload, headers=headers)
    client.post("/api/v1/pistoleos", json=payload, headers=headers)

    audit = client.get("/api/v1/auditoria?limite=50", headers=headers)
    assert audit.status_code == 200, audit.text
    pistoleos = [
        item for item in audit.json()
        if item["entidad"] == "PISTOLEO" and (item["datos_nuevos"] or {}).get("codigo_bulto") == codigo_bulto
    ]
    incidencias = [
        item for item in audit.json()
        if item["entidad"] == "INCIDENCIA" and (item["datos_nuevos"] or {}).get("codigo_bulto") == codigo_bulto
    ]
    assert any(item["datos_nuevos"]["estado"] == "OK" for item in pistoleos)
    assert any(item["datos_nuevos"]["estado"] == "DUPLICADO" for item in pistoleos)
    assert any(item["datos_nuevos"].get("codigo_hoja") == codigo_hoja for item in pistoleos)
    assert any(item["accion"] == "CREAR" for item in incidencias)


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


def test_migrar_conserva_el_pistoleo_en_la_hoja_destino():
    client = TestClient(app)
    headers = authenticated_client(client)
    origen = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-23",
            "ruta": "Origen Pistoleado",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    destino = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-23",
            "ruta": "Destino Pistoleado",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    bulto = client.post(
        "/api/v1/bultos",
        json={"codigo": f"BU{uuid4().int % 90000000 + 10000000}", "hoja_ruta_id": origen.json()["id"]},
        headers=headers,
    )
    pistoleo = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": bulto.json()["codigo"], "hoja_ruta_id": origen.json()["id"]},
        headers=headers,
    )
    assert pistoleo.status_code == 201, pistoleo.text

    moved = client.post(
        "/api/v1/reasignaciones",
        json={
            "bulto_id": bulto.json()["id"],
            "hoja_destino_id": destino.json()["id"],
            "motivo": "Migración con pistoleo",
        },
        headers=headers,
    )
    assert moved.status_code == 201, moved.text

    bulto_destino = client.get(f"/api/v1/bultos/{bulto.json()['id']}", headers=headers)
    assert bulto_destino.json()["hoja_ruta_id"] == destino.json()["id"]
    assert bulto_destino.json()["pistoleado"] is True
    assert bulto_destino.json()["estado"] == "OK"

    repetido = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": bulto.json()["codigo"], "hoja_ruta_id": destino.json()["id"]},
        headers=headers,
    )
    assert repetido.status_code == 201, repetido.text
    assert repetido.json()["estado"] == "DUPLICADO"


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

    origin_after = client.get(f"/api/v1/hojas-ruta/{origin.json()['id']}", headers=headers)
    assert origin_after.status_code == 200, origin_after.text
    assert origin_after.json()["estado"] == "INACTIVA"
    assert origin_after.json()["cantidad_bultos"] == 0
    assert origin_after.json()["cantidad_declarada"] == 1

    destination_after = client.get(f"/api/v1/hojas-ruta/{destination.json()['id']}", headers=headers)
    assert destination_after.status_code == 200, destination_after.text
    assert destination_after.json()["estado"] == "ACTIVA"
    assert destination_after.json()["cantidad_bultos"] == 1


def test_reassignment_keeps_origin_active_when_bultos_remain():
    client = TestClient(app)
    headers = authenticated_client(client)
    origin = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-25",
            "ruta": "Ruta Origen Parcial",
            "cantidad_declarada": 2,
        },
        headers=headers,
    )
    destination = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRE-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRE",
            "fecha": "2026-09-25",
            "ruta": "Ruta Destino Parcial",
            "cantidad_declarada": 1,
        },
        headers=headers,
    )
    origin_id = origin.json()["id"]
    for _ in range(2):
        created = client.post(
            "/api/v1/bultos",
            json={
                "codigo": f"BU{uuid4().int % 90000000 + 10000000}",
                "hoja_ruta_id": origin_id,
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
    first_id = created.json()["id"]

    response = client.post(
        "/api/v1/reasignaciones",
        json={
            "bulto_id": first_id,
            "hoja_destino_id": destination.json()["id"],
            "motivo": "Se mueve solo un bulto",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text

    origin_after = client.get(f"/api/v1/hojas-ruta/{origin_id}", headers=headers)
    assert origin_after.json()["estado"] == "ACTIVA"
    assert origin_after.json()["cantidad_bultos"] == 1


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


def test_hojas_bultos_y_pistoleos_quedan_aislados_por_usuario():
    client = TestClient(app)
    codigo = f"HRD-2026-{uuid4().int % 9000 + 1000}"
    codigo_bulto = f"BU{uuid4().int % 90000000 + 10000000}"
    payload = {
        "codigo": codigo,
        "tipo": "HRD",
        "fecha": "2026-09-15",
        "ruta": "Ruta Propia",
        "cantidad_declarada": 1,
    }
    headers_a = authenticated_client(client)
    headers_b = authenticated_client(client)

    hoja_a = client.post("/api/v1/hojas-ruta", json=payload, headers=headers_a)
    assert hoja_a.status_code == 201, hoja_a.text
    hoja_b = client.post("/api/v1/hojas-ruta", json=payload, headers=headers_b)
    assert hoja_b.status_code == 201, hoja_b.text
    assert hoja_a.json()["id"] != hoja_b.json()["id"]
    assert hoja_a.json()["usuario_id"] != hoja_b.json()["usuario_id"]

    bulto_a = client.post(
        "/api/v1/bultos",
        json={"codigo": codigo_bulto, "hoja_ruta_id": hoja_a.json()["id"]},
        headers=headers_a,
    )
    assert bulto_a.status_code == 201, bulto_a.text

    lista_b = client.get("/api/v1/hojas-ruta", headers=headers_b)
    assert lista_b.status_code == 200, lista_b.text
    assert hoja_a.json()["id"] not in {item["id"] for item in lista_b.json()}

    ajeno = client.get(f"/api/v1/bultos/{bulto_a.json()['id']}", headers=headers_b)
    assert ajeno.status_code == 404, ajeno.text

    pistoleo = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": codigo_bulto, "hoja_ruta_id": hoja_b.json()["id"]},
        headers=headers_b,
    )
    assert pistoleo.status_code == 201, pistoleo.text
    assert pistoleo.json()["estado"] == "SIN LISTA ESPERADA"
    assert pistoleo.json()["usuario_id"] != hoja_a.json()["usuario_id"]


def _hoja_con_bulto_ajeno(client: TestClient, headers: dict[str, str]):
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
    pistoleo = client.post(
        "/api/v1/pistoleos",
        json={"codigo_bulto": bulto.json()["codigo"], "hoja_ruta_id": destino.json()["id"]},
        headers=headers,
    )
    assert pistoleo.status_code == 201, pistoleo.text
    incidencias = client.get("/api/v1/incidencias?estado=PENDIENTE", headers=headers)
    incidencia = next(item for item in incidencias.json() if item["bulto_id"] == bulto.json()["id"])
    return origen.json(), destino.json(), bulto.json(), incidencia


def test_resolver_no_pertenece_elimina_el_pistoleo():
    client = TestClient(app)
    headers = authenticated_client(client)
    origen, destino, bulto, incidencia = _hoja_con_bulto_ajeno(client, headers)

    response = client.post(
        f"/api/v1/incidencias/{incidencia['id']}/resolver",
        json={"accion": "ELIMINAR_PISTOLEO"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["estado"] == "ANULADO"
    assert response.json()["observaciones"] == "Pistoleo eliminado"
    moved = client.get(f"/api/v1/bultos/{bulto['id']}", headers=headers)
    assert moved.json()["hoja_ruta_id"] == origen["id"]
    reporte = client.get(f"/api/v1/reportes/hoja-ruta/{destino['id']}", headers=headers)
    assert reporte.status_code == 200, reporte.text
    assert reporte.json()["no_pertenece"] == 0


def test_resolver_no_pertenece_anade_el_bulto_a_la_hoja():
    client = TestClient(app)
    headers = authenticated_client(client)
    _origen, destino, bulto, incidencia = _hoja_con_bulto_ajeno(client, headers)

    response = client.post(
        f"/api/v1/incidencias/{incidencia['id']}/resolver",
        json={"accion": "ANADIR_BULTO"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["estado"] == "REASIGNADO"
    assert response.json()["observaciones"] == "El bulto se cambió a esta ruta"
    moved = client.get(f"/api/v1/bultos/{bulto['id']}", headers=headers)
    assert moved.status_code == 200, moved.text
    assert moved.json()["hoja_ruta_id"] == destino["id"]
    assert moved.json()["pistoleado"] is True
    assert moved.json()["estado"] == "OK"
    origen = client.get(f"/api/v1/hojas-ruta/{_origen['id']}", headers=headers)
    assert origen.status_code == 200, origen.text
    assert origen.json()["estado"] == "ACTIVA"
    assert origen.json()["cantidad_bultos"] == 0
    reporte = client.get(f"/api/v1/reportes/hoja-ruta/{destino['id']}", headers=headers)
    assert reporte.json()["no_pertenece"] == 0


def test_resolver_anade_solo_el_bulto_pistoleado_y_conserva_el_resto():
    client = TestClient(app)
    headers = authenticated_client(client)
    origen, destino, bulto, incidencia = _hoja_con_bulto_ajeno(client, headers)
    companero = client.post(
        "/api/v1/bultos",
        json={
            "codigo": f"BU{uuid4().int % 90000000 + 10000000}",
            "hoja_ruta_id": origen["id"],
        },
        headers=headers,
    )
    assert companero.status_code == 201, companero.text

    response = client.post(
        f"/api/v1/incidencias/{incidencia['id']}/resolver",
        json={"accion": "ANADIR_BULTO"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    lista = client.get("/api/v1/bultos", headers=headers)
    en_origen = [item for item in lista.json() if item["hoja_ruta_id"] == origen["id"]]
    en_destino = [item for item in lista.json() if item["hoja_ruta_id"] == destino["id"]]
    assert [item["codigo"] for item in en_origen] == [companero.json()["codigo"]]
    assert [item["codigo"] for item in en_destino] == [bulto["codigo"]]
    hoja_origen = client.get(f"/api/v1/hojas-ruta/{origen['id']}", headers=headers)
    assert hoja_origen.json()["estado"] == "ACTIVA"
    assert hoja_origen.json()["cantidad_bultos"] == 1
