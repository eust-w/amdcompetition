from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .artifacts import write_run
from .backends.analytic import AnalyticBackend
from .backends.genesis_backend import GenesisBackend
from .config import load_config
from .runner import run_benchmark


def create_backend(name: str, success_height_m: float, strict_single_gpu: bool):
    if name == "analytic":
        return AnalyticBackend()
    return GenesisBackend(name, success_height_m, strict_single_gpu)


class DashboardHandler(SimpleHTTPRequestHandler):
    project_root: Path
    runs_root: Path
    config_path: Path
    backend_name: str
    evaluation_lock = threading.Lock()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"status": "ok", "backend": self.backend_name})
            return
        if path == "/api/latest":
            try:
                run_dir = self._latest_run_dir()
                payload = {
                    "report": self._read_json(run_dir / "report.json"),
                    "manifest": self._read_json(run_dir / "manifest.json"),
                }
                certificate_path = self.runs_root / "reproducibility.json"
                if certificate_path.exists():
                    payload["reproducibility"] = self._read_json(certificate_path)
                self._json(payload)
            except (FileNotFoundError, ValueError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            return
        if path.startswith("/api/artifacts/"):
            filename = Path(path).name
            if filename not in {"report.json", "manifest.json", "episodes.jsonl", "summary.md", "config.json"}:
                self._json({"error": "artifact not allowed"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                artifact = self._latest_run_dir() / filename
                payload = artifact.read_bytes()
            except FileNotFoundError as exc:
                self._json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json" if filename.endswith(".json") else "text/plain")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(payload)
            return
        if path != "/" and not (Path(self.directory or "") / path.lstrip("/")).exists():
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/evaluate":
            self._json({"error": "route not found"}, HTTPStatus.NOT_FOUND)
            return
        if not self.evaluation_lock.acquire(blocking=False):
            self._json({"error": "evaluation already running"}, HTTPStatus.CONFLICT)
            return
        try:
            config = load_config(self.config_path)
            backend = create_backend(self.backend_name, config.success_height_m, config.strict_single_gpu)
            result = run_benchmark(config, backend)
            run_dir, report = write_run(self.project_root, self.runs_root, config, result)
            self._json({"run_dir": str(run_dir), "report": report}, HTTPStatus.CREATED)
        except Exception as exc:  # API boundary: return a structured failure to the UI.
            self._json({"error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
        finally:
            self.evaluation_lock.release()

    def _latest_run_dir(self) -> Path:
        run_id = (self.runs_root / "LATEST").read_text(encoding="utf-8").strip()
        if not run_id or Path(run_id).name != run_id:
            raise ValueError("invalid LATEST run id")
        return self.runs_root / run_id

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"dashboard: {format % args}")


def serve_dashboard(
    project_root: Path,
    host: str,
    port: int,
    config_path: Path,
    runs_root: Path,
    backend_name: str,
) -> None:
    dashboard_dist = project_root / "dashboard" / "dist"
    if not (dashboard_dist / "index.html").exists():
        raise FileNotFoundError("dashboard/dist is missing; run `npm --prefix dashboard run build`")

    def handler(*args, **kwargs):
        instance = DashboardHandler(*args, directory=str(dashboard_dist), **kwargs)
        return instance

    DashboardHandler.project_root = project_root
    DashboardHandler.runs_root = runs_root
    DashboardHandler.config_path = config_path
    DashboardHandler.backend_name = backend_name
    server = ThreadingHTTPServer((host, port), handler)
    print(f"RoboRecover dashboard: http://{host}:{port}")
    print(f"Evaluation backend: {backend_name}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
