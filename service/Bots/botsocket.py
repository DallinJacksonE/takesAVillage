# service/Bots/botsocket.py

from websocket_router import (
    manager,
    process_game_event
)


class BotSocket:

    def __init__(
        self,
        game,
        game_id: str,
        user_id: str
    ):
        self.game = game
        self.game_id = game_id
        self.user_id = user_id

        self.on_game_state = None
        self.on_chat_history = None
        self.on_new_chat_message = None
        self.on_game_started = None
        self.on_error = None

    # ---------------------------------------
    # RECEIVING EVENTS
    # ---------------------------------------

    async def send_json(self, packet):

        event = packet.get("event")
        data = packet.get("data")

        if event == "game_state":
            if self.on_game_state:
                await self.on_game_state(data)

        elif event == "chat_history":
            if self.on_chat_history:
                await self.on_chat_history(data)

        elif event == "new_chat_message":
            if self.on_new_chat_message:
                await self.on_new_chat_message(data)

        elif event == "game_started":
            if self.on_game_started:
                await self.on_game_started()

        elif event == "error":
            if self.on_error:
                await self.on_error(data)

    # ---------------------------------------
    # JOIN ROOM
    # ---------------------------------------

    async def connect(self):

        await manager.connect(
            self,
            self.game_id,
            self.user_id
        )

        await manager.send_personal_message(
            {
                "event": "chat_history",
                "data": self.game.get_private_chat_history(
                    self.user_id
                )
            },
            self.game_id,
            self.user_id
        )

        await manager.send_personal_message(
            {
                "event": "game_state",
                "data": self.game.get_state_for_player(
                    self.user_id
                )
            },
            self.game_id,
            self.user_id
        )

    async def disconnect(self):

        manager.disconnect(
            self,
            self.game_id,
            self.user_id
        )

    # ---------------------------------------
    # OUTGOING EVENTS
    # ---------------------------------------

    async def request_update(self):

        await process_game_event(
            "request_update",
            {},
            self.game_id,
            self.user_id,
            self.game
        )

    async def send_chat(
        self,
        content: str,
        to_id: str = "GLOBAL"
    ):

        await process_game_event(
            "send_chat",
            {
                "content": content,
                "to_id": to_id
            },
            self.game_id,
            self.user_id,
            self.game
        )

    async def submit_action(
        self,
        payload: dict
    ):

        await process_game_event(
            "submit_action",
            payload,
            self.game_id,
            self.user_id,
            self.game
        )

    async def create_chat(
        self,
        name: str,
        member_ids: list[str]
    ):

        await process_game_event(
            "create_chat",
            {
                "name": name,
                "memberIds": member_ids
            },
            self.game_id,
            self.user_id,
            self.game
        )