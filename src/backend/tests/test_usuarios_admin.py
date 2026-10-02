from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin-fixture@example.com", "password": "SecurePass123!", "rol": "ADMIN"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_session_survives_changing_the_signed_in_email():
    client = TestClient(app)
    headers = admin_headers(client)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    original = me.json()["email"]
    nuevo = f"admin-{uuid4().hex[:8]}@example.com"

    try:
        updated = client.put(
            f"/api/v1/usuarios/{me.json()['id']}",
            json={
                "nombre": me.json()["nombre"],
                "apellido": me.json()["apellido"],
                "email": nuevo,
                "rol": "ADMIN",
            },
            headers=headers,
        )
        assert updated.status_code == 200, updated.text
        listed = client.get("/api/v1/usuarios", headers=headers)
        assert listed.status_code == 200, listed.text
    finally:
        client.put(
            f"/api/v1/usuarios/{me.json()['id']}",
            json={
                "nombre": me.json()["nombre"],
                "apellido": me.json()["apellido"],
                "email": original,
                "rol": "ADMIN",
            },
            headers=headers,
        )


def test_login_rejects_mismatched_access_type():
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin-fixture@example.com", "password": "SecurePass123!", "rol": "AUDITOR"},
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Tu cuenta no posee permisos de auditor"


def test_admin_manages_users_permissions_and_activity():
    client = TestClient(app)
    headers = admin_headers(client)
    email = f"equipo-{uuid4().hex[:8]}@example.com"
    codigo = f"HRD-2026-{uuid4().int % 9000 + 1000}"

    created = client.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Equipo",
            "apellido": "Campo",
            "email": email,
            "password": "SecurePass123!",
            "rol": "AUDITOR",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    usuario_id = created.json()["id"]
    assert created.json()["rol"] == "AUDITOR"
    assert created.json()["activo"] is True

    denied = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!", "rol": "ADMIN"},
    )
    assert denied.status_code == 403, denied.text
    auditor = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!", "rol": "AUDITOR"},
    )
    assert auditor.status_code == 200, auditor.text
    auditor_headers = {"Authorization": f"Bearer {auditor.json()['access_token']}"}
    forbidden = client.get("/api/v1/usuarios", headers=auditor_headers)
    assert forbidden.status_code == 403, forbidden.text

    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": codigo,
            "tipo": "HRD",
            "fecha": "2026-10-01",
            "ruta": "Ruta del auditor",
            "cantidad_declarada": 1,
        },
        headers=auditor_headers,
    )
    assert hoja.status_code == 201, hoja.text

    activity = client.get(f"/api/v1/usuarios/{usuario_id}/actividad", headers=headers)
    assert activity.status_code == 200, activity.text
    body = activity.json()
    assert body["total_hojas"] == 1
    assert body["hojas"][0]["codigo"] == codigo
    assert body["total_pistoleos"] == 0

    updated = client.put(
        f"/api/v1/usuarios/{usuario_id}",
        json={
            "nombre": "Equipo",
            "apellido": "Campo",
            "email": email,
            "rol": "ADMIN",
        },
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["rol"] == "ADMIN"

    inactive = client.patch(
        f"/api/v1/usuarios/{usuario_id}/estado",
        json={"activo": False},
        headers=headers,
    )
    assert inactive.status_code == 200, inactive.text
    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!", "rol": "ADMIN"},
    )
    assert blocked.status_code == 401, blocked.text

    active = client.patch(
        f"/api/v1/usuarios/{usuario_id}/estado",
        json={"activo": True},
        headers=headers,
    )
    assert active.status_code == 200, active.text

    removed = client.delete(f"/api/v1/usuarios/{usuario_id}", headers=headers)
    assert removed.status_code == 409, removed.text

    self_delete = client.get("/api/v1/auth/me", headers=headers)
    own = client.delete(f"/api/v1/usuarios/{self_delete.json()['id']}", headers=headers)
    assert own.status_code == 409, own.text


def test_archivar_oculta_registros_del_auditor_y_eliminar_hoja_conserva_el_historial():
    client = TestClient(app)
    headers = admin_headers(client)
    email = f"archivo-{uuid4().hex[:8]}@example.com"
    created = client.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Ada",
            "apellido": "Campo",
            "email": email,
            "password": "SecurePass123!",
            "rol": "AUDITOR",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    auditor = created.json()
    session = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!", "rol": "AUDITOR"},
    )
    assert session.status_code == 200, session.text
    auditor_headers = {"Authorization": f"Bearer {session.json()['access_token']}"}
    hoja = client.post(
        "/api/v1/hojas-ruta",
        json={
            "codigo": f"HRD-2026-{uuid4().int % 9000 + 1000}",
            "tipo": "HRD",
            "fecha": "2026-09-29",
            "ruta": "Ruta a archivar",
            "cantidad_declarada": 1,
        },
        headers=auditor_headers,
    )
    assert hoja.status_code == 201, hoja.text
    bulto = client.post(
        "/api/v1/bultos",
        json={"codigo": f"BU{uuid4().int % 90000000 + 10000000}", "hoja_ruta_id": hoja.json()["id"]},
        headers=auditor_headers,
    )
    assert bulto.status_code == 201, bulto.text

    archived = client.post(f"/api/v1/usuarios/{auditor['id']}/archivar", headers=headers)
    assert archived.status_code == 200, archived.text
    assert archived.json()["archivadas"] == 1
    visibles = client.get("/api/v1/hojas-ruta", headers=auditor_headers)
    assert visibles.json() == []
    actividad = client.get(f"/api/v1/usuarios/{auditor['id']}/actividad", headers=headers)
    assert actividad.status_code == 200, actividad.text
    assert actividad.json()["hojas"][0]["situacion"] == "ARCHIVADO"

    removed = client.delete(f"/api/v1/usuarios/{auditor['id']}/hojas/{hoja.json()['id']}", headers=headers)
    assert removed.status_code == 200, removed.text
    despues = client.get(f"/api/v1/usuarios/{auditor['id']}/actividad", headers=headers)
    assert despues.json()["hojas"][0]["situacion"] == "ELIMINADO"
    assert client.get("/api/v1/bultos", headers=auditor_headers).json() == []
