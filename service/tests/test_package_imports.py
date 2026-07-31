import importlib


def test_service_and_bot_loggers_import_without_top_level_collision():
    service_logging = importlib.import_module("service.logging")
    bot_logging = importlib.import_module("bots.logger")

    assert service_logging.BackendLogger.__module__ == "service.logging"
    assert bot_logging.Logger.__module__ == "bots.logger"
