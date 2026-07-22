import json
from pathlib import Path

from roborecover.artifacts import sha256_file, write_run
from roborecover.backends.analytic import AnalyticBackend
from roborecover.config import load_config
from roborecover.runner import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_artifact_manifest_matches_written_files(tmp_path: Path) -> None:
    config = load_config(ROOT / "configs" / "smoke.json")
    result = run_benchmark(config, AnalyticBackend())
    run_dir, report = write_run(ROOT, tmp_path, config, result)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert (tmp_path / "LATEST").read_text(encoding="utf-8").strip() == report["run_id"]
    for filename, record in manifest["files"].items():
        path = run_dir / filename
        assert record["sha256"] == sha256_file(path)
        assert record["bytes"] == path.stat().st_size
    assert report["backend_evidence"]["rocm_verified"] is False

