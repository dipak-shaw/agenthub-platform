"""Exercise public API using an ASGI transport and temporary SQLite."""

import json

from httpx import ASGITransport, AsyncClient

from agent_hub.main import create_app


async def test_chat_crud(settings):
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/health")).json()["model_mode"] == "demo"
            assert len((await client.get("/api/agents")).json()) == 2
            response = await client.post(
                "/api/agents/search-bot/chat", json={"message": "search latest news"}
            )
            assert response.status_code == 200
            events = [
                json.loads(line[6:])
                for line in response.text.splitlines()
                if line.startswith("data: ")
            ]
            assert events[-1]["status"] == "complete", events
            assert "tool_start" in [event["type"] for event in events]
            cid = events[0]["conversation_id"]
            detail = (await client.get(f"/api/conversations/{cid}")).json()
            assert len(detail["messages"]) == 2
            assert detail["messages"][-1]["sources"]
            assert "[1]" in detail["messages"][-1]["content"]
            assert (
                await client.patch(f"/api/conversations/{cid}", json={"title": "Renamed"})
            ).json()["title"] == "Renamed"
            regen = await client.post(
                "/api/agents/search-bot/chat",
                json={"conversation_id": cid, "message": "ignored", "regenerate": True},
            )
            assert "run_finished" in regen.text
            assert len((await client.get(f"/api/conversations/{cid}")).json()["messages"]) == 2
            assert (await client.delete(f"/api/conversations/{cid}")).status_code == 204
            assert (await client.get(f"/api/conversations/{cid}")).status_code == 404
