from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

try:
    from .runtime_manager import LiveRuntimeManager
except ImportError:
    from runtime.web_backend.runtime_manager import LiveRuntimeManager


def create_app(args) -> FastAPI:
    app = FastAPI(title="InsightFace RKNN Web Demo", version="1.0.0")
    manager = LiveRuntimeManager(args)
    frontend_dist = Path(args.frontend_dist).resolve()
    index_path = frontend_dist / "index.html"
    assets_path = frontend_dist / "assets"

    @app.on_event("startup")
    def on_startup():
        manager.start()

    @app.on_event("shutdown")
    def on_shutdown():
        manager.stop()

    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    @app.get("/api/health")
    def api_health():
        return {"ok": True}

    @app.get("/api/status")
    def api_status():
        payload = manager.describe_runtime()
        payload["available_model_packs"] = manager.list_model_packs()
        return payload

    @app.get("/api/live-state")
    def api_live_state():
        return manager.describe_live_state()

    @app.get("/api/live-state/stream")
    def api_live_state_stream():
        def event_generator():
            last_payload = ""
            last_keepalive = time.perf_counter()
            interval = max(0.02, 1.0 / max(1, args.live_state_fps))
            while not manager.stop_event.is_set():
                payload = json.dumps(manager.describe_live_state(), ensure_ascii=False)
                if payload != last_payload:
                    yield f"event: state\ndata: {payload}\n\n"
                    last_payload = payload
                    last_keepalive = time.perf_counter()
                else:
                    now = time.perf_counter()
                    if now - last_keepalive >= 1.0:
                        yield ": keep-alive\n\n"
                        last_keepalive = now
                time.sleep(interval)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/model-packs")
    def api_model_packs():
        return {"items": manager.list_model_packs()}

    @app.post("/api/model-pack/select")
    def api_model_pack_select(payload: dict = Body(...)):
        model_pack = str(payload.get("model_pack", "")).strip()
        if not model_pack:
            raise HTTPException(status_code=400, detail="model_pack 값이 비었습니다.")
        try:
            return manager.switch_model(model_pack)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/gallery/people")
    def api_gallery_people():
        return {"items": manager.list_people()}

    @app.post("/api/gallery/people")
    def api_gallery_create_person(payload: dict = Body(...)):
        name_ko = str(payload.get("name_ko", "")).strip()
        name_en = str(payload.get("name_en", "")).strip()
        if not name_ko:
            raise HTTPException(status_code=400, detail="name_ko 값이 비었습니다.")
        try:
            person = manager.create_person(name_ko=name_ko, name_en=name_en)
            return {"item": person}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/gallery/people/{person_id}")
    def api_gallery_update_person(person_id: str, payload: dict = Body(...)):
        name_ko = str(payload.get("name_ko", "")).strip()
        name_en = str(payload.get("name_en", "")).strip()
        if not name_ko:
            raise HTTPException(status_code=400, detail="name_ko 값이 비었습니다.")
        try:
            person = manager.update_person(person_id=person_id, name_ko=name_ko, name_en=name_en)
            return {"item": person}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/gallery/people/{person_id}")
    def api_gallery_delete_person(person_id: str):
        try:
            manager.delete_person(person_id)
            return {"ok": True}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/gallery/people/{person_id}/images/capture")
    def api_gallery_capture_person_image(person_id: str):
        try:
            image = manager.capture_person_image(person_id)
            return {"item": image}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/gallery/people/{person_id}/images/upload")
    async def api_gallery_upload_person_image(person_id: str, files: list[UploadFile] = File(...)):
        saved = []
        try:
            for upload in files:
                content = await upload.read()
                saved.append(manager.save_uploaded_image(person_id, content, upload.filename or "upload.jpg"))
            return {"items": saved}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/gallery/people/{person_id}/images/{image_id}")
    def api_gallery_delete_person_image(person_id: str, image_id: str):
        try:
            manager.delete_person_image(person_id, image_id)
            return {"ok": True}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/gallery/people/{person_id}/images/{image_id}/file")
    def api_gallery_person_image_file(person_id: str, image_id: str):
        try:
            return FileResponse(manager.get_person_image_path(person_id, image_id))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/gallery/reload")
    def api_gallery_reload():
        manager.reload_gallery()
        return {"ok": True}

    @app.get("/api/snapshot.jpg")
    def api_snapshot():
        try:
            return StreamingResponse(iter([manager.get_snapshot_bytes()]), media_type="image/jpeg")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/stream.mjpg")
    def stream_mjpg():
        def frame_generator():
            while not manager.stop_event.is_set():
                frame = manager.get_stream_frame()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
                time.sleep(max(0.0, 1.0 / max(1, args.stream_fps)))

        return StreamingResponse(
            frame_generator(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    @app.get("/")
    def frontend_index():
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse("<h1>frontend build가 아직 없습니다.</h1>", status_code=503)

    @app.get("/{path_name:path}")
    def frontend_fallback(path_name: str):
        if path_name.startswith("api/") or path_name == "stream.mjpg":
            raise HTTPException(status_code=404, detail="not found")
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse({"detail": "frontend build가 아직 없습니다."}, status_code=503)

    return app
