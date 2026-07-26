from models import Crab, CrabLogs, BatchCrab


class TestCrabsGetAll:
    def test_without_auth_returns_401(self, client):
        resp = client.get("/api/v1/crabs/")
        assert resp.status_code == 401

    def test_empty_list(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_with_crabs(self, client, access_token, app, db_session):
        db_session.add_all([
            Crab(name="Crab A", group_by="A"),
            Crab(name="Crab B", group_by="B"),
        ])
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        assert data[0]["name"] == "Crab A"
        assert data[1]["name"] == "Crab B"


class TestCrabsBatch:
    def test_get_batches_without_auth(self, client):
        resp = client.get("/api/v1/crabs/batch")
        assert resp.status_code == 401

    def test_get_batches_empty(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/batch")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_get_batches_with_data(self, client, access_token, app, db_session):
        db_session.add(BatchCrab(user_id=1))
        db_session.add(BatchCrab(user_id=1))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/batch")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        assert data[0]["description"].startswith("BATCH-")

    def test_create_batch_without_auth(self, client):
        resp = client.post("/api/v1/crabs/batch")
        assert resp.status_code == 401

    def test_create_batch_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        resp = client.post("/api/v1/crabs/batch")
        assert resp.status_code == 201
        body = resp.json()
        assert body["detail"] == "Batch created successfully"
        assert body["data"]["user_id"] == 1
        assert body["data"]["description"].startswith("BATCH-")


class TestCrabsGroup:
    def test_without_auth(self, client):
        resp = client.get("/api/v1/crabs/A")
        assert resp.status_code == 401

    def test_filter_by_group(self, client, access_token, app, db_session):
        db_session.add_all([
            Crab(name="Alpha", group_by="A"),
            Crab(name="Beta", group_by="B"),
            Crab(name="Gamma", group_by="A"),
        ])
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/A")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        assert all(c["group_by"] == "A" for c in data)


class TestCrabsLogs:
    def test_insert_without_auth(self, client):
        resp = client.post("/api/v1/crabs/logs")
        assert resp.status_code == 401

    def test_insert_log_success(self, client, access_token, app, db_session):
        db_session.add(Crab(name="Test Crab", group_by="A"))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.post("/api/v1/crabs/logs", json={
            "crab_id": 1,
            "type": "actual",
            "width": 10.5,
            "weight": 400.0
        })
        assert resp.status_code == 201
        assert resp.json()["detail"] == "Crab log inserted successfully"

    def test_get_logs_by_type_without_auth(self, client):
        resp = client.get("/api/v1/crabs/logs/actual")
        assert resp.status_code == 401

    def test_get_logs_by_type_empty_returns_404(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/logs/actual")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "No logs found matching criteria"

    def test_get_logs_by_type_with_data(self, client, access_token, app, db_session):
        crab = Crab(name="Log Crab", group_by="A")
        db_session.add(crab)
        db_session.commit()

        db_session.add(CrabLogs(crab_id=crab.id, type="actual", width=10.0, weight=400.0, user_id=1, batch_id=1))
        db_session.add(CrabLogs(crab_id=crab.id, type="actual", width=11.0, weight=410.0, user_id=1, batch_id=1))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/crabs/logs/actual")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        assert data[0]["crab_name"] == "Log Crab"

    def test_get_logs_by_crab_id(self, client, access_token, app, db_session):
        crab = Crab(name="Specific Crab", group_by="B")
        db_session.add(crab)
        db_session.commit()

        db_session.add(CrabLogs(crab_id=crab.id, type="actual", width=12.0, weight=500.0, user_id=1, batch_id=1))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get(f"/api/v1/crabs/logs/actual/{crab.id}/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["crab_id"] == crab.id
