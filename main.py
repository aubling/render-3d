from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List
from pathlib import Path
import subprocess, tempfile

app = FastAPI(title="Kitchen Blender Render API", version="1.0.0")

class Unit(BaseModel):
    unit_type: str
    width: int
    height: int
    depth: int
    color: str = "Pearl Grey"
    doors: int = 1

class RenderRequest(BaseModel):
    project_id: int
    units: List[Unit]

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/render-3d")
def render_3d(data: RenderRequest):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        request_file = p / "request.json"
        output_file = p / f"kitchen_render_{data.project_id}.png"
        request_file.write_text(data.model_dump_json(), encoding="utf-8")

        result = subprocess.run(
            ["blender", "-b", "--python", "/app/blender_renderer.py", "--", str(request_file), str(output_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=240
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={"message": "Blender render failed", "stderr": result.stderr[-3000:]}
            )

        if not output_file.exists():
            raise HTTPException(status_code=500, detail="PNG was not created")

        return Response(content=output_file.read_bytes(), media_type="image/png")
