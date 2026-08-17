async def _send_queued_notifications(game, game_id, manager):
    if not hasattr(game, "drain_notifications"):
        return
    for player_id in list(getattr(game, "players", {}).keys()):
        for notification in game.drain_notifications(player_id):
            await manager.send_personal_message({
                "event": "game_notification",
                "data": notification,
            }, game_id, player_id)


async def process_game_event(event, payload, game_id, user_id, game, manager):
    if event == "start_game_request":
        if game.host_id == user_id and game.start_game():
            await manager.broadcast_to_game(
                {"event": "game_started", "data": {"day": 1}}, game_id)
            await manager.broadcast_game_state(game_id, game)
    elif event == "request_update":
        await manager.send_personal_message(
            {"event": "game_state", "data": game.get_state_for_player(user_id)},
            game_id, user_id)
    elif event == "send_chat":
        message = game.handle_chat(user_id, payload)
        if message:
            data = message.to_dict()
            group_chat = next(
                (chat for chat in game.chats if chat.id == message.to_id), None)
            if message.to_id == "GLOBAL":
                await manager.broadcast_to_game(
                    {"event": "new_chat_message", "data": data}, game_id)
            elif group_chat:
                packet = {"event": "new_chat_message", "data": data}
                for member_id in group_chat.member_ids:
                    await manager.send_personal_message(
                        packet, game_id, member_id)
            else:
                packet = {"event": "new_chat_message", "data": data}
                await manager.send_personal_message(packet, game_id, message.from_id)
                await manager.send_personal_message(packet, game_id, message.to_id)
    elif event == "submit_action":
        if game.status == "WAITING":
            return
        command = payload.get("action_command", payload.get("actionId"))
        player = game.players.get(user_id)
        if command == "FINISH_PHASE" and player and player.finished_phase:
            return
        if game.handle_action(user_id, payload):
            await _send_queued_notifications(game, game_id, manager)
            await manager.broadcast_game_state(game_id, game)
        else:
            await manager.send_personal_message({
                "event": "error",
                "data": {"message": "Action rejected by game rules.",
                         "action_command": command},
            }, game_id, user_id)
    elif event == "create_chat":
        if game.create_chat(user_id, payload["name"], payload["memberIds"]):
            await manager.broadcast_game_state(game_id, game)
