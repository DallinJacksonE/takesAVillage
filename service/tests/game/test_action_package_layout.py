import importlib


def test_packet_handling_domain_is_available_through_focused_package_paths():
    base = importlib.import_module("service.game.packet_handling.base")
    development = importlib.import_module(
        "service.game.packet_handling.development"
    )
    work = importlib.import_module("service.game.packet_handling.work")
    conflict = importlib.import_module("service.game.packet_handling.conflict")
    campfire = importlib.import_module("service.game.packet_handling.campfire")
    contracts = importlib.import_module("service.game.packet_handling.contracts")
    contract_service = importlib.import_module(
        "service.game.packet_handling.contract_service"
    )
    dispatcher = importlib.import_module(
        "service.game.packet_handling.dispatcher"
    )
    phase_resolution = importlib.import_module(
        "service.game.packet_handling.phase_resolution"
    )

    assert base.Command.__module__ == "service.game.packet_handling.base"
    assert development.BuildDevelopmentCommand.__module__ == (
        "service.game.packet_handling.development"
    )
    assert work.CommitWorkCommand.__module__ == (
        "service.game.packet_handling.work"
    )
    assert conflict.ContestDevelopmentCommand.__module__ == (
        "service.game.packet_handling.conflict"
    )
    assert campfire.StartFireCommand.__module__ == (
        "service.game.packet_handling.campfire"
    )
    assert contracts.TradeContract.__module__ == (
        "service.game.packet_handling.contracts"
    )
    assert contract_service.ContractFactory.__module__ == (
        "service.game.packet_handling.contract_service"
    )
    assert dispatcher.PacketDispatcher.__module__ == (
        "service.game.packet_handling.dispatcher"
    )
    assert phase_resolution.PhaseResolver.__module__ == (
        "service.game.packet_handling.phase_resolution"
    )
