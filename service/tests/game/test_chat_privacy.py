import asyncio

from service.api.websocket.game_events import process_game_event


class RecordingManager:
    def __init__(self):
        self.broadcasts = []
        self.personal = []

    async def broadcast_to_game(self, message, game_id):
        self.broadcasts.append((message, game_id))

    async def send_personal_message(self, message, game_id, user_id):
        self.personal.append((message, game_id, user_id))


async def _send(game, manager, user_id, to_id, content="secret"):
    await process_game_event(
        "send_chat",
        {"content": content, "to_id": to_id},
        game.id,
        user_id,
        game,
        manager,
    )


def test_group_chat_is_delivered_only_to_members_and_restored_in_history(make_game):
    game = make_game()
    game.add_player("player-3")
    chat = game.create_chat(
        "player-1", "private", ["player-1", "player-2"])
    manager = RecordingManager()

    asyncio.run(_send(game, manager, "player-1", chat.id))

    assert manager.broadcasts == []
    assert {entry[2] for entry in manager.personal} == {"player-1", "player-2"}
    assert len(game.get_private_chat_history("player-2")) == 1
    assert game.get_private_chat_history("player-3") == []


def test_non_member_cannot_send_to_group_chat(make_game):
    game = make_game()
    game.add_player("player-3")
    chat = game.create_chat(
        "player-1", "private", ["player-1", "player-2"])
    manager = RecordingManager()

    asyncio.run(_send(game, manager, "player-3", chat.id))

    assert manager.broadcasts == []
    assert manager.personal == []
    assert game.chat_messages == []


def test_chat_creation_rejects_unknown_members(make_game):
    game = make_game()

    assert game.create_chat(
        "player-1", "invalid", ["player-2", "missing-player"]
    ) is None
    assert game.chats == []
