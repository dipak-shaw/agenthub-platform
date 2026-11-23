"""Serve the compiled SPA without masking API errors or exposing arbitrary files."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


def mount_web(app: FastAPI, root: Path) -> None:
    @app.get("/{path:path}", include_in_schema=False)
    async def web(path: str) -> FileResponse:
        if path.split("/")[0] in {"api", "health"}:
            raise HTTPException(404, "Not found")
        target = (root / path).resolve()
        if not target.is_relative_to(root.resolve()):
            raise HTTPException(404, "Not found")
        if target.is_file():
            return FileResponse(target)
        if Path(path).suffix or not (root / "index.html").is_file():
            raise HTTPException(404, "Web app not built; run make web-build")
        return FileResponse(root / "index.html")
