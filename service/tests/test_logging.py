import logging

from service.logging import BackendLogger


def test_backend_logger_falls_back_when_repo_log_directory_is_not_writable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    blocked_dir = tmp_path / "logs" / "system"
    blocked_dir.mkdir(parents=True)
    blocked_dir.chmod(0o555)

    try:
        logger = BackendLogger("fallback-test")
        logger.info("can write somewhere")
    finally:
        blocked_dir.chmod(0o755)
        logging.getLogger("fallback-test").handlers.clear()

    assert logger.log_dir != str(blocked_dir)
