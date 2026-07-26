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
