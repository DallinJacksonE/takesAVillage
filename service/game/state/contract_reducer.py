"""Contract event appliers for the game-state reducer."""


class ContractReducer:
    def _apply_contract_created(self, game, event):
        return self._publish_contract_to_players(game, event.contract)

    def _apply_contract_updated(self, game, event):
        return self._publish_contract_to_players(game, event.contract)

    def _publish_contract_to_players(self, game, contract):
        initiator = game.players.get(contract.initiator_id)
        target = game.players.get(contract.target_id)
        if initiator:
            initiator.actions[contract.id] = contract
        if target:
            target.actions[contract.id] = contract
        return contract

    def _apply_contract_removed(self, game, event):
        for player in game.players.values():
            player.actions.pop(event.contract_id, None)
        return event.contract_id

    def _apply_contract_expired(self, game, event):
        contract = None
        for player in game.players.values():
            contract = player.actions.get(event.contract_id)
            if contract:
                break
        if not contract:
            return None
        contract.status = "EXPIRED"
        contract.waiting_on_id = None
        return self._publish_contract_to_players(game, contract)

    def _apply_trade_finalized(self, game, event):
        contract = None
        for player in game.players.values():
            contract = player.actions.get(event.contract_id)
            if contract:
                break
        if event.initiator_lied and contract:
            game.lie_count[contract.initiator_id] = (
                game.lie_count.get(contract.initiator_id, 0) + 1
            )
        if event.target_lied and contract:
            game.lie_count[contract.target_id] = (
                game.lie_count.get(contract.target_id, 0) + 1
            )
        game.trade_count += 1
        return contract

    def _apply_employment_accepted(self, game, event):
        worker = game.players.get(event.worker_id)
        development = game.developments.get(event.development_id)
        if not worker or not development:
            return None
        job = {
            "development": development.to_dict(),
            "wage": event.wage,
            "wage_type": event.wage_type,
            "employer_id": event.employer_id,
            "action_id": event.contract_id,
        }
        worker.available_work.append(job)
        return job
