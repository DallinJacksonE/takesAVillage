import importlib


def test_action_domain_is_available_through_focused_package_paths():
    base = importlib.import_module("service.game.actions.base")
    development = importlib.import_module(
        "service.game.actions.development"
    )
    work = importlib.import_module("service.game.actions.work")
    conflict = importlib.import_module("service.game.actions.conflict")
    campfire = importlib.import_module("service.game.actions.campfire")
    contracts = importlib.import_module("service.game.actions.contracts")
    contract_service = importlib.import_module(
        "service.game.actions.contract_service"
    )
    dispatcher = importlib.import_module(
        "service.game.actions.dispatcher"
    )
    phase_resolution = importlib.import_module(
        "service.game.actions.phase_resolution"
    )

    assert base.Command.__module__ == "service.game.actions.base"
    assert development.BuildDevelopmentCommand.__module__ == (
        "service.game.actions.development"
    )
    assert work.CommitWorkCommand.__module__ == "service.game.actions.work"
    assert conflict.ContestDevelopmentCommand.__module__ == (
        "service.game.actions.conflict"
    )
    assert campfire.StartFireCommand.__module__ == (
        "service.game.actions.campfire"
    )
    assert contracts.TradeContract.__module__ == (
        "service.game.actions.contracts"
    )
    assert contract_service.ContractFactory.__module__ == (
        "service.game.actions.contract_service"
    )
    assert dispatcher.ActionDispatcher.__module__ == (
        "service.game.actions.dispatcher"
    )
    assert phase_resolution.PhaseResolver.__module__ == (
        "service.game.actions.phase_resolution"
    )
