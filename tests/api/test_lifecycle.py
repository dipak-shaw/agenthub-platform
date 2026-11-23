"""Cancellation, failure persistence, isolation, routes, and static serving."""

import pytest
from httpx import ASGITransport, AsyncClient

from agent_hub.core.errors import HubError
from agent_hub.core.loop_engines.basic import BasicEngine
from agent_hub.core.testing import scripted_model
from agent_hub.main import create_app


async def test_stop_disconnect_and_history(settings):
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        service = app.state.chat
        service.engine = lambda agent: BasicEngine(
            agent, settings, scripted_model(["partial", " later"], 0.025)
        )
        run = await service.start("plain-bot", "First question", None, True, False)
        events = service.events(run)
        assert (await anext(events)).type == "run_started"
        assert (await anext(events)).text == "partial"
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            assert (
                await client.delete(f"/api/conversations/{run.conversation_id}")
            ).status_code == 400
            assert (await client.post(f"/api/runs/{run.id}/stop")).status_code == 204
        remaining = [e async for e in events]
        assert [e.type for e in remaining] == ["error", "run_finished"]
        saved = await app.state.repository.get(run.conversation_id)
        assert saved.messages[-1].content == "partial"
        assert saved.messages[-1].status == "stopped"
        # A follow-up builds model history from this conversation only.
        run2 = await service.start("plain-bot", "Second question", run.conversation_id, True, False)
        stream = service.events(run2)
        await anext(stream)
        await anext(stream)
        await stream.aclose()
        saved = await app.state.repository.get(run.conversation_id)
        assert len(saved.messages) == 4 and saved.messages[-1].status == "stopped"
        assert not service.runs
        # Stop immediately, before the producer has taken its first event-loop turn.
        immediate = await service.start("plain-bot", "Immediate", None, True, False)
        await service.stop(immediate.id)
        assert (await app.state.repository.get(immediate.conversation_id)).messages[
            -1
        ].status == "stopped"


async def test_failure_and_busy(settings):
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        service = app.state.chat
        service.engine = lambda agent: BasicEngine(
            agent, settings, scripted_model(["part"], 0.01, ValueError("secret must not leak"))
        )
        run = await service.start("plain-bot", "question", None, True, False)
        with pytest.raises(HubError, match="already running"):
            await service.start("plain-bot", "second", run.conversation_id, True, False)
        events = [e async for e in service.events(run)]
        assert events[-1].status == "error"
        assert "secret must not leak" not in str(events)
        detail = await app.state.repository.get(run.conversation_id)
        assert detail.messages[-1].content == "part"
        assert detail.messages[-1].error_code == "model_unavailable"
        assert detail.messages[-1].model == "scripted"
        with pytest.raises(HubError):
            await service.stop(run.id)

        def broken(agent):
            raise ValueError("private error")

        service.engine = broken
        run = await service.start("plain-bot", "broken factory", None, True, False)
        assert [e async for e in service.events(run)][-1].status == "error"


async def test_route_errors_and_static(settings, tmp_path):
    settings.web_dist = tmp_path / "web"
    settings.web_dist.mkdir()
    (settings.web_dist / "index.html").write_text("<html>App</html>")
    (settings.web_dist / "asset.js").write_text("app")
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            assert (await client.get("/api/agents/plain-bot")).json()["name"] == "plain-bot"
            for path in [
                "/api/agents/no-agent",
                "/api/agents/plain-bot/avatar",
                "/api/conversations/missing",
                "/api/unknown",
                "/unknown.js",
            ]:
                assert (await client.get(path)).status_code == 404
            assert (await client.get("/")).text == "<html>App</html>"
            assert (await client.get("/agents/plain-bot")).status_code == 200
            assert (await client.get("/asset.js")).text == "app"
            assert (await client.post("/api/runs/missing/stop")).status_code == 404
            assert (
                await client.patch("/api/conversations/missing", json={"title": "New"})
            ).status_code == 404
            assert (await client.delete("/api/conversations/missing")).status_code == 404
            assert (
                await client.patch("/api/conversations/missing", json={"title": " "})
            ).status_code == 422
            assert (
                await client.post("/api/agents/plain-bot/chat", json={"message": "", "unknown": 1})
            ).status_code == 422
            assert (
                await client.post("/api/agents/plain-bot/chat", json={"message": "x" * 16001})
            ).status_code == 400
            assert (
                await client.post(
                    "/api/agents/plain-bot/chat", json={"message": "x", "regenerate": True}
                )
            ).status_code == 404
            assert (await client.get("/api/conversations?agent=plain-bot")).json() == []
            assert (
                await client.post(
                    "/api/agents/plain-bot/chat", json={"message": "x", "conversation_id": "absent"}
                )
            ).status_code == 404
        # Wrong agent must never append to a conversation.
        record, _, _ = await app.state.repository.prepare(
            "plain-bot", None, "hello", "hello", False
        )
        with pytest.raises(HubError):
            await app.state.repository.prepare("search-bot", record.id, "x", "x", False)
        await app.state.repository.finish("missing", "", [], "complete", None, "demo", 0, 0, 0)


async def test_avatar_route_and_invalid_startup(settings, tmp_path):
    import shutil

    shutil.copytree("tests/fixtures/agents/plain-bot", tmp_path / "agents/plain-bot")
    settings.agents_dir = tmp_path / "agents"
    p = settings.agents_dir / "plain-bot/agent.yaml"
    p.write_text(p.read_text().replace("avatar: 💬", "avatar: avatar.svg"))
    (p.parent / "avatar.svg").write_text("<svg/>")
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.get("/api/agents/plain-bot/avatar")
            assert (
                response.status_code == 200
                and "sandbox" in response.headers["content-security-policy"]
            )
    p.write_text("bad: true")
    with pytest.raises(HubError):
        async with app.router.lifespan_context(app):
            pass


async def test_db_configuration(tmp_path):
    from agent_hub.core.storage.db import create_database

    with pytest.raises(ValueError):
        create_database("postgresql://invalid")
