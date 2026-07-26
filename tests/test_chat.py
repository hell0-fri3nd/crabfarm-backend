from unittest.mock import patch, MagicMock
from models import ChatSession, ChatMessage


class TestChatSessions:
    def test_create_without_auth(self, client):
        resp = client.post("/api/v1/ai/chat/sessions")
        assert resp.status_code == 401

    def test_create_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        resp = client.post("/api/v1/ai/chat/sessions")
        assert resp.status_code == 201
        body = resp.json()
        assert body["detail"] == "Session created"
        assert body["data"]["status"] == "active"
        assert "id" in body["data"]

    def test_get_without_auth(self, client):
        resp = client.get("/api/v1/ai/chat/sessions/fake-id")
        assert resp.status_code == 401

    def test_get_not_found(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.get("/api/v1/ai/chat/sessions/non-existent-id")
        assert resp.status_code == 404

    def test_get_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        create_resp = client.post("/api/v1/ai/chat/sessions")
        session_id = create_resp.json()["data"]["id"]

        client.cookies.set("access_token", access_token)
        resp = client.get(f"/api/v1/ai/chat/sessions/{session_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == session_id
        assert body["data"]["status"] == "active"


class TestChatMessages:
    def test_send_without_auth(self, client):
        resp = client.post("/api/v1/ai/chat/sessions/fake/messages")
        assert resp.status_code == 401

    def test_send_missing_content(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        create_resp = client.post("/api/v1/ai/chat/sessions")
        session_id = create_resp.json()["data"]["id"]

        client.cookies.set("access_token", access_token)
        resp = client.post(
            f"/api/v1/ai/chat/sessions/{session_id}/messages",
            json={}
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Missing content"

    def test_send_to_nonexistent_session(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        resp = client.post(
            "/api/v1/ai/chat/sessions/non-existent/messages",
            json={"content": "Hello"}
        )
        assert resp.status_code == 404

    def test_send_message_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        create_resp = client.post("/api/v1/ai/chat/sessions")
        session_id = create_resp.json()["data"]["id"]

        client.cookies.set("access_token", access_token)
        resp = client.post(
            f"/api/v1/ai/chat/sessions/{session_id}/messages",
            json={"content": "Hello AI"}
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["detail"] == "Message sent"
        assert body["data"]["message"] == "success"
        assert body["data"]["user_message"]["content"] == "Hello AI"
        assert "assistant_message" in body["data"]


class TestChatEndSession:
    def test_end_without_auth(self, client):
        resp = client.patch("/api/v1/ai/chat/sessions/fake/end")
        assert resp.status_code == 401

    def test_end_not_found(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.patch("/api/v1/ai/chat/sessions/non-existent/end")
        assert resp.status_code == 404

    def test_end_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        create_resp = client.post("/api/v1/ai/chat/sessions")
        session_id = create_resp.json()["data"]["id"]

        client.cookies.set("access_token", access_token)
        resp = client.patch(f"/api/v1/ai/chat/sessions/{session_id}/end")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Session ended"

    def test_send_to_ended_session(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        create_resp = client.post("/api/v1/ai/chat/sessions")
        session_id = create_resp.json()["data"]["id"]

        client.cookies.set("access_token", access_token)
        client.patch(f"/api/v1/ai/chat/sessions/{session_id}/end")

        client.cookies.set("access_token", access_token)
        resp = client.post(
            f"/api/v1/ai/chat/sessions/{session_id}/messages",
            json={"content": "Hello"}
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Session has ended"


class TestChatDeleteSession:
    def test_delete_without_auth(self, client):
        resp = client.delete("/api/v1/ai/chat/sessions/fake")
        assert resp.status_code == 401

    def test_delete_not_found(self, client, access_token):
        client.cookies.set("access_token", access_token)
        resp = client.delete("/api/v1/ai/chat/sessions/non-existent")
        assert resp.status_code == 404

    def test_delete_success(self, client, access_token, app):
        client.cookies.set("access_token", access_token)
        create_resp = client.post("/api/v1/ai/chat/sessions")
        session_id = create_resp.json()["data"]["id"]

        client.cookies.set("access_token", access_token)
        resp = client.delete(f"/api/v1/ai/chat/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Session deleted"
