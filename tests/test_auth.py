from models import Users


class TestAuthRoot:
    def test_health_check(self, client):
        resp = client.get("/api/v1/auth/")
        assert resp.status_code == 200
        data = resp.json()
        assert "Hello Friend" in data["message"]


class TestAuthStatus:
    def test_without_tokens_returns_400(self, client):
        resp = client.get("/api/v1/auth/status")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "MISSING_REFRESH_TOKEN"

    def test_with_refresh_only_returns_401(self, client, refresh_token, access_token):
        client.cookies.set("refresh_token", refresh_token)
        client.cookies.set("access_token", "invalid")
        resp = client.get("/api/v1/auth/status")
        assert resp.status_code == 401

    def test_with_invalid_tokens(self, client):
        client.cookies.set("refresh_token", "bad-token")
        client.cookies.set("access_token", "bad-token")
        resp = client.get("/api/v1/auth/status")
        assert resp.status_code in (400, 401)


class TestAuthLogin:
    def test_missing_email(self, client):
        resp = client.post("/api/v1/auth/login", json={"password": "pass"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing parameter: email"

    def test_missing_password(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "test@test.com"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing parameter: password"

    def test_email_not_found(self, client, app):
        resp = client.post("/api/v1/auth/login", json={
            "email": "unknown@test.com",
            "password": "pass"
        })
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Email not found"

    def test_incorrect_password(self, client, app, db_session):
        user = Users(
            name="Test",
            email="test@test.com",
            password="correct-password",
            pin="1234",
            role="admin"
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "wrong-password"
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect password"

    def test_successful_login(self, client, app, db_session):
        user = Users(
            name="Test User",
            email="success@test.com",
            password="secret",
            pin="4321",
            role="admin"
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post("/api/v1/auth/login", json={
            "email": "success@test.com",
            "password": "secret"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["detail"] == "Login Successfuly"
        assert body["data"]["email"] == "success@test.com"
        assert body["data"]["name"] == "Test User"
        assert body["data"]["role"] == "admin"

        cookies = resp.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_login_with_remember_me(self, client, app, db_session):
        user = Users(
            name="Remember",
            email="remember@test.com",
            password="pass",
            pin="1111",
            role="user"
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post("/api/v1/auth/login", json={
            "email": "remember@test.com",
            "password": "pass",
            "remember_me": True
        })
        assert resp.status_code == 200
        assert "refresh_token" in resp.cookies


class TestAuthPin:
    def test_missing_refresh_token(self, client):
        resp = client.post("/api/v1/auth/pin", json={"pin": "1234"})
        assert resp.status_code == 400

    def test_missing_pin(self, client, refresh_token):
        client.cookies.set("refresh_token", refresh_token)
        resp = client.post("/api/v1/auth/pin", json={})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing parameter: PIN"

    def test_successful_pin(self, client, app, db_session):
        user = Users(
            name="Pin User",
            email="pin@test.com",
            password="pass",
            pin="9999",
            role="admin"
        )
        db_session.add(user)
        db_session.commit()

        from services import JWTManager
        jwt = JWTManager()
        token = jwt.create_refresh_token({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        })

        client.cookies.set("refresh_token", token)
        resp = client.post("/api/v1/auth/pin", json={"pin": "9999"})
        assert resp.status_code == 200


class TestAuthLogout:
    def test_logout(self, client, app, db_session):
        user = Users(
            name="Logout User",
            email="logout@test.com",
            password="pass",
            pin="0000",
            role="user"
        )
        db_session.add(user)
        db_session.commit()

        from services import JWTManager
        jwt = JWTManager()
        token = jwt.create_refresh_token({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        })

        client.cookies.set("refresh_token", token)
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Successfully logged out"

    def test_logout_all(self, client):
        resp = client.post("/api/v1/auth/logout-all")
        assert resp.status_code == 200
        assert "Clear-Site-Data" in resp.headers


def _create_user(db_session, **kwargs):
    user = Users(
        name=kwargs.get("name", "Profile User"),
        email=kwargs.get("email", "profile@test.com"),
        password=kwargs.get("password", "pass"),
        pin=kwargs.get("pin", "1234"),
        role=kwargs.get("role", "user")
    )
    db_session.add(user)
    db_session.commit()
    return user


def _make_tokens(user):
    from services import JWTManager
    jwt = JWTManager()
    payload = {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
    return jwt.create_access_token(payload), jwt.create_refresh_token(payload)


def _set_tokens(client, access_token, refresh_token):
    client.cookies.set("access_token", access_token)
    client.cookies.set("refresh_token", refresh_token)


class TestAuthProfile:
    def test_get_profile_missing_tokens(self, client):
        resp = client.get("/api/v1/auth/profile")
        assert resp.status_code == 400

    def test_get_profile_success(self, client, app, db_session):
        user = _create_user(db_session, email="get-profile@test.com", role="admin")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.get("/api/v1/auth/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["detail"] == "Profile retrieved successfully"
        assert body["data"]["name"] == user.name
        assert body["data"]["email"] == user.email
        assert body["data"]["role"] == user.role
        assert "id" in body["data"]
        assert "created_at" in body["data"]
        assert "updated_at" in body["data"]

    def test_update_profile_missing_name(self, client, app, db_session):
        user = _create_user(db_session, email="update-profile@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.patch("/api/v1/auth/profile", json={})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing parameter: name"

    def test_update_profile_success(self, client, app, db_session):
        user = _create_user(db_session, email="update-name@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.patch("/api/v1/auth/profile", json={"name": "New Name"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["detail"] == "Profile updated successfully"
        assert body["data"]["name"] == "New Name"

    def test_update_password_success(self, client, app, db_session):
        user = _create_user(db_session, email="update-pass@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.patch("/api/v1/auth/profile/password", json={"password": "newpass"})
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Password/Pin updated successfully"

    def test_update_pin_success(self, client, app, db_session):
        user = _create_user(db_session, email="update-pin@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.patch("/api/v1/auth/profile/password", json={"pin": "5678"})
        assert resp.status_code == 200

    def test_update_password_pin_missing_both(self, client, app, db_session):
        user = _create_user(db_session, email="missing-both@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.patch("/api/v1/auth/profile/password", json={})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing parameter: password or pin"


class TestAuthAdminUsers:
    def test_get_users_non_admin(self, client, app, db_session):
        user = _create_user(db_session, email="non-admin@test.com", role="user")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.get("/api/v1/auth/profile/user")
        assert resp.status_code == 403

    def test_get_users_success(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-list@test.com", role="admin")
        _create_user(db_session, email="other1@test.com", name="Other One")
        _create_user(db_session, email="other2@test.com", name="Other Two")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.get("/api/v1/auth/profile/user")
        assert resp.status_code == 200
        body = resp.json()
        assert body["detail"] == "Users retrieved successfully"
        emails = [u["email"] for u in body["data"]]
        assert "other1@test.com" in emails
        assert "other2@test.com" in emails
        assert "admin-list@test.com" not in emails

    def test_delete_user_non_admin(self, client, app, db_session):
        user = _create_user(db_session, email="del-non-admin@test.com", role="user")
        target = _create_user(db_session, email="target@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.delete(f"/api/v1/auth/profile/user/{target.id}")
        assert resp.status_code == 403

    def test_delete_user_success(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-del@test.com", role="admin")
        target = _create_user(db_session, email="delete-me@test.com")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.delete(f"/api/v1/auth/profile/user/{target.id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "User deleted successfully"

    def test_delete_user_not_found(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-del-nf@test.com", role="admin")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.delete("/api/v1/auth/profile/user/99999")
        assert resp.status_code == 404

    def test_add_user_non_admin(self, client, app, db_session):
        user = _create_user(db_session, email="add-non-admin@test.com", role="user")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.post("/api/v1/auth/profile/user", json={
            "name": "New User", "email": "new@test.com"
        })
        assert resp.status_code == 403

    def test_add_user_success(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-add@test.com", role="admin")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.post("/api/v1/auth/profile/user", json={
            "name": "New User", "email": "new-user@test.com"
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["detail"] == "User created successfully"
        assert body["data"]["name"] == "New User"
        assert body["data"]["email"] == "new-user@test.com"

    def test_add_user_missing_fields(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-add-missing@test.com", role="admin")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.post("/api/v1/auth/profile/user", json={"name": "No Email"})
        assert resp.status_code == 400

    def test_add_user_duplicate_email(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-add-dup@test.com", role="admin")
        _create_user(db_session, email="duplicate@test.com")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.post("/api/v1/auth/profile/user", json={
            "name": "Dup", "email": "duplicate@test.com"
        })
        assert resp.status_code == 409

    def test_reset_credentials_success(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-reset@test.com", role="admin")
        target = _create_user(db_session, email="reset-me@test.com")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.put(f"/api/v1/auth/profile/user/{target.id}", json={
            "reset_password": True, "reset_pin": True
        })
        assert resp.status_code == 200
        assert resp.json()["detail"] == "User credentials reset successfully"

    def test_reset_credentials_missing_fields(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-reset-miss@test.com", role="admin")
        target = _create_user(db_session, email="reset-miss@test.com")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.put(f"/api/v1/auth/profile/user/{target.id}", json={})
        assert resp.status_code == 400

    def test_update_role_non_admin(self, client, app, db_session):
        user = _create_user(db_session, email="role-non-admin@test.com", role="user")
        target = _create_user(db_session, email="role-target@test.com")
        at, rt = _make_tokens(user)
        _set_tokens(client, at, rt)
        resp = client.put(f"/api/v1/auth/profile/user/{target.id}/role", json={"role": "admin"})
        assert resp.status_code == 403

    def test_update_role_success(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-role@test.com", role="admin")
        target = _create_user(db_session, email="role-change@test.com", role="user")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.put(f"/api/v1/auth/profile/user/{target.id}/role", json={"role": "admin"})
        assert resp.status_code == 200
        assert resp.json()["detail"] == "User role updated successfully"

    def test_update_role_invalid_value(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-role-bad@test.com", role="admin")
        target = _create_user(db_session, email="role-bad@test.com")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.put(f"/api/v1/auth/profile/user/{target.id}/role", json={"role": "superadmin"})
        assert resp.status_code == 400

    def test_update_role_missing_field(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-role-miss@test.com", role="admin")
        target = _create_user(db_session, email="role-miss@test.com")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.put(f"/api/v1/auth/profile/user/{target.id}/role", json={})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing parameter: role"

    def test_update_role_user_not_found(self, client, app, db_session):
        admin = _create_user(db_session, email="admin-role-nf@test.com", role="admin")
        at, rt = _make_tokens(admin)
        _set_tokens(client, at, rt)
        resp = client.put("/api/v1/auth/profile/user/99999/role", json={"role": "admin"})
        assert resp.status_code == 404
