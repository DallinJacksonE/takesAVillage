import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def write_config(path: Path, bots: object) -> None:
    path.write_text(json.dumps({"bots": bots}), encoding="utf-8")


def test_loads_bot_secret_and_service_urls_from_json(monkeypatch, tmp_path):
    config_path = tmp_path / "service.json"
    write_config(config_path, {
        "secret": "test-secret",
        "httpUrl": "http://bots:8001",
        "gameServerHttpUrl": "http://service:5000",
        "gameServerWsUrl": "ws://service:5000/ws",
    })
    monkeypatch.setenv("SERVICE_CONFIG_PATH", str(config_path))
    config.get_service_config.cache_clear()

    assert config.get_bot_config() == {
        "secret": "test-secret",
        "httpUrl": "http://bots:8001",
        "gameServerHttpUrl": "http://service:5000",
        "gameServerWsUrl": "ws://service:5000/ws",
    }


def test_rejects_malformed_json_without_exposing_file_contents(monkeypatch, tmp_path):
    config_path = tmp_path / "service.json"
    config_path.write_text('{"bots":{"secret":"do-not-leak"', encoding="utf-8")
    monkeypatch.setenv("SERVICE_CONFIG_PATH", str(config_path))
    config.get_service_config.cache_clear()

    with pytest.raises(RuntimeError, match="Unable to load bot service configuration") as exc:
        config.get_bot_config()

    assert "do-not-leak" not in str(exc.value)


@pytest.mark.parametrize("missing_key", [
    "secret",
    "httpUrl",
    "gameServerHttpUrl",
    "gameServerWsUrl",
])
def test_rejects_missing_required_bot_configuration(monkeypatch, tmp_path, missing_key):
    values = {
        "secret": "test-secret",
        "httpUrl": "http://bots:8001",
        "gameServerHttpUrl": "http://service:5000",
        "gameServerWsUrl": "ws://service:5000/ws",
    }
    del values[missing_key]
    config_path = tmp_path / "service.json"
    write_config(config_path, values)
    monkeypatch.setenv("SERVICE_CONFIG_PATH", str(config_path))
    config.get_service_config.cache_clear()

    with pytest.raises(RuntimeError, match=f"bots.{missing_key}"):
        config.get_bot_config()


def test_bot_server_fails_startup_when_secret_is_missing(tmp_path):
    config_path = tmp_path / "service.json"
    write_config(config_path, {
        "httpUrl": "http://bots:8001",
        "gameServerHttpUrl": "http://service:5000",
        "gameServerWsUrl": "ws://service:5000/ws",
    })
    environment = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        "SERVICE_CONFIG_PATH": str(config_path),
    }

    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "bots.secret" in result.stderr
