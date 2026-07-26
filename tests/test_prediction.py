from models import CrabLogs, BatchCrab


class TestPredictionRoot:
    def test_server_status(self, client):
        resp = client.get("/api/v1/predictions/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "server running"


class TestPredictionGet:
    def test_without_auth(self, client):
        resp = client.get("/api/v1/predictions/1")
        assert resp.status_code == 401

    def test_no_logs_found(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/predictions/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "No logs found for prediction"

    def test_successful_prediction(self, client, access_token, app, db_session):
        crab_id = 1
        for i in range(7):
            db_session.add(CrabLogs(
                crab_id=crab_id,
                type="actual",
                width=10.0 + i * 0.5,
                weight=400.0 + i * 10.0,
                user_id=1
            ))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get(f"/api/v1/predictions/{crab_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "Predicted" in body["detail"]
        assert len(body["data"]) == 7
        for entry in body["data"]:
            assert "crab_id" in entry
            assert "width" in entry
            assert "weight" in entry


class TestPredictionPost:
    def test_without_auth(self, client):
        resp = client.post("/api/v1/predictions/1")
        assert resp.status_code == 401

    def test_no_actual_logs_found(self, client, access_token, app, db_session):
        client.cookies.set("access_token", access_token)
        resp = client.post("/api/v1/predictions/999", json={"batch_id": 1})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "No logs found for prediction"

    def test_successful_insert(self, client, access_token, app, db_session):
        batch = BatchCrab(user_id=1)
        db_session.add(batch)
        db_session.commit()

        crab_id = 1
        for i in range(7):
            db_session.add(CrabLogs(
                crab_id=crab_id,
                type="actual",
                width=10.0 + i * 0.5,
                weight=400.0 + i * 10.0,
                user_id=1,
                batch_id=batch.id
            ))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.post(f"/api/v1/predictions/{crab_id}", json={"batch_id": batch.id})
        assert resp.status_code == 201
        body = resp.json()
        assert "inserted successfully" in body["detail"]

    def test_duplicate_prediction(self, client, access_token, app, db_session):
        batch = BatchCrab(user_id=1)
        db_session.add(batch)
        db_session.commit()

        crab_id = 2
        for i in range(7):
            db_session.add(CrabLogs(
                crab_id=crab_id,
                type="actual",
                width=10.0 + i * 0.5,
                weight=400.0 + i * 10.0,
                user_id=1,
                batch_id=batch.id
            ))
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.post(f"/api/v1/predictions/{crab_id}", json={"batch_id": batch.id})
        assert resp.status_code == 201

        client.cookies.set("access_token", access_token)
        resp = client.post(f"/api/v1/predictions/{crab_id}", json={"batch_id": batch.id})
        assert resp.status_code == 200
        assert resp.json()["detail"] == "this crab already has predictions for the next 7 days"
