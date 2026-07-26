from models import ActivityLogs, SensorLogs, Users


class TestActivityLogsGet:
    def test_without_auth(self, client):
        resp = client.get("/api/v1/logs/")
        assert resp.status_code == 401

    def test_empty_list(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/logs/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_with_logs(self, client, access_token, app, db_session):
        user = Users(name="Logger", email="log@test.com", password="p", pin="12", role="admin")
        db_session.add(user)
        db_session.commit()

        db_session.add(ActivityLogs(
            activity_type="auth",
            description="User logged in",
            user_id=user.id
        ))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/logs/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["activity_type"] == "auth"
        assert data[0]["description"] == "User logged in"
        assert data[0]["user_id"] == user.id


class TestActivityLogsPost:
    def test_without_auth(self, client):
        resp = client.post("/api/v1/logs/")
        assert resp.status_code == 401

    def test_insert_log(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        resp = client.post("/api/v1/logs/", json={
            "activity_type": "sensors",
            "description": "Test activity",
            "value": 42.0
        })
        assert resp.status_code == 201
        assert resp.json()["detail"] == "Activity log inserted successfully"


class TestSensorLogs:
    def test_without_auth(self, client):
        resp = client.get("/api/v1/logs/sensor")
        assert resp.status_code == 401

    def test_empty_sensor_logs(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/logs/sensor")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_with_sensor_logs(self, client, access_token, app, db_session):
        db_session.add(SensorLogs(
            sensor_type="temperature",
            status="NORMAL",
            value=28.5
        ))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/logs/sensor")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["sensor_type"] == "temperature"
        assert data[0]["value"] == 28.5
