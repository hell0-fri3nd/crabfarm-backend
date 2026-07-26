from models import SchedulerSettings


class TestSettingsSchedules:
    def test_get_without_auth(self, client):
        resp = client.get("/api/v1/settings/schedules")
        assert resp.status_code == 401

    def test_get_empty(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/settings/schedules")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_get_with_schedules(self, client, access_token, app, db_session):
        db_session.add_all([
            SchedulerSettings(type="feeding", scheduler_type="daily", hour=8, is_enabled=True, user_id=1),
            SchedulerSettings(type="valve", scheduler_type="weekly", hour=12, is_enabled=False, user_id=1),
        ])
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/settings/schedules")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        types = {s["type"] for s in data}
        assert types == {"feeding", "valve"}

    def test_post_without_auth(self, client):
        resp = client.post("/api/v1/settings/schedules")
        assert resp.status_code == 401

    def test_post_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        resp = client.post("/api/v1/settings/schedules", json={
            "type": "feeding",
            "scheduler_type": "daily",
            "hour": 8,
            "is_enabled": True,
            "seconds": 0,
        })
        assert resp.status_code == 201
        assert resp.json()["detail"] == "New Schedules inserted successfully"

    def test_put_missing_id(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.put("/api/v1/settings/schedules", json={})
        assert resp.status_code == 422
        assert resp.json()["detail"] == "Schedule ID is required for update"

    def test_put_not_found(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.put("/api/v1/settings/schedules", json={"id": 999, "hour": 10})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Schedule not found"

    def test_put_update(self, client, access_token, app, db_session):
        schedule = SchedulerSettings(
            type="feeding", scheduler_type="daily", hour=8,
            is_enabled=True, user_id=1
        )
        db_session.add(schedule)
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.put("/api/v1/settings/schedules", json={
            "id": schedule.id,
            "hour": 14,
            "is_enabled": False
        })
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Schedule updated successfully"

    def test_delete_without_auth(self, client):
        resp = client.delete("/api/v1/settings/schedules/1")
        assert resp.status_code == 401

    def test_delete_not_found(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.delete("/api/v1/settings/schedules/999")
        assert resp.status_code == 404

    def test_delete_success(self, client, access_token, app, db_session):
        schedule = SchedulerSettings(
            type="valve", scheduler_type="custom", hour=0,
            seconds=3600, is_enabled=True, user_id=1
        )
        db_session.add(schedule)
        db_session.commit()

        client.cookies.set("access_token", access_token)
        resp = client.delete(f"/api/v1/settings/schedules/{schedule.id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Schedule deleted successfully"
