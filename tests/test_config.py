from pathlib import Path

from roborecover.config import load_config


ROOT = Path(__file__).resolve().parents[1]


def test_smoke_config_is_valid() -> None:
    config = load_config(ROOT / "configs" / "smoke.json")
    assert config.episode_count == 9
    assert sum(config.failure_mix.values()) == 1.0
    assert config.strict_single_gpu is True

