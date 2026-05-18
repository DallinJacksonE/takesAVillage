class EconomyResolvers:
    @staticmethod
    def resolve_work_phase(game_state):
        DEV_OUTPUT_MAP = {"Farm": "food", "Woods": "wood", "Mine": "iron"}

        for player in game_state.players.values():
            if player.health in ["sick", "recovering"]:
                continue
            ca = getattr(player, 'committed_action', None)
            if ca and isinstance(ca, dict):
                dev_data = ca.get('development', {})
                owner_id = dev_data.get('owner_id')
                dev_type = dev_data.get('type')
                dev_level = int(dev_data.get('level', 1))
                is_working_for_other = (owner_id != player.session_id)

                owner = game_state.players.get(owner_id)
                resource_produced = DEV_OUTPUT_MAP.get(dev_type)

                if owner and resource_produced:
                    # 1. Base Yield Generation (Owner gets EVERYTHING)
                    owner.resources[resource_produced] = owner.resources.get(
                        resource_produced, 0) + dev_level

                    # 2. Add a timeline event so the owner knows
                    # they generated goods from someone else's labor
                    if is_working_for_other:
                        owner.add_timeline_event("LABOR_EXPLOITED",
                                                 {"worker":
                                                  player.session_id,
                                                  "yield": dev_level,
                                                  "type": resource_produced})
