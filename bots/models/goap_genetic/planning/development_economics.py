from dataclasses import dataclass

from ..memory import Memory


RESOURCE_TYPES = ("food", "wood", "iron")
DEVELOPMENT_RESOURCE = {"Farm": "food", "Woods": "wood", "Mine": "iron"}


@dataclass(frozen=True)
class DevelopmentEconomist:
    """Derives factual economics for owned and target developments."""

    at_risk_maintenance_days: float = 3.0

    def resource_for_type(self, dev_type: str | None) -> str | None:
        if dev_type is None:
            return None
        return DEVELOPMENT_RESOURCE.get(dev_type)

    def production_per_labor(self, dev: dict) -> float:
        try:
            return max(0.0, float(dev.get("level", 1) or 1))
        except (TypeError, ValueError):
            return 1.0

    def expected_laborers(self, dev: dict, memory: Memory) -> float:
        dev_id = dev.get("id")
        owner_id = dev.get("owner_id")
        my_id = memory.get("my_id")
        workers = set()

        if owner_id:
            workers.add(owner_id)
        elif my_id:
            workers.add(my_id)

        for job in memory.get("available_work", []) or []:
            development = job.get("development", {}) or {}
            if dev_id and development.get("id") != dev_id:
                continue
            employer_id = job.get("employer_id") or development.get("owner_id")
            if employer_id == my_id:
                workers.add(my_id)

        for contract in memory.get("pending_contracts", []) or []:
            if contract.get("type") != "EMPLOYMENT" or contract.get("status") != "ACCEPTED":
                continue
            if dev_id and contract.get("dev_id") != dev_id:
                continue
            worker_id = (
                contract.get("initiator_id")
                if contract.get("is_application", True)
                else contract.get("target_id")
            )
            if worker_id:
                workers.add(worker_id)

        return max(1.0, float(len(workers)))

    def remaining_work_days(self, memory: Memory) -> float:
        game_length = float(memory.get("game_length", 0) or 0)
        day = float(memory.get("day", 0) or 0)
        if game_length <= 0:
            return 1.0
        return max(1.0, game_length - day)

    def upgrade_marginal_output(self, dev: dict, memory: Memory) -> dict[str, float]:
        resource = self.resource_for_type(dev.get("type"))
        if not resource:
            return {}
        if dev.get("can_upgrade") is False:
            return {}
        value = self.expected_laborers(
            dev, memory) * self.remaining_work_days(memory)
        return {resource: value} if value > 0.0 else {}

    def maintenance_loss_risk(self, dev: dict, memory: Memory) -> float:
        try:
            days = float(dev.get("maintenance_days", 0) or 0)
        except (TypeError, ValueError):
            days = 0.0
        if days <= 1.0:
            urgency = 1.0
        elif days <= self.at_risk_maintenance_days:
            urgency = (self.at_risk_maintenance_days - days +
                       1.0) / self.at_risk_maintenance_days
        else:
            urgency = 0.0
        output = self.production_per_labor(
            dev) * self.expected_laborers(dev, memory)
        return urgency * max(1.0, output)

    def maintenance_required_resources(self, memory: Memory) -> dict[str, float]:
        deficits: dict[str, float] = {}
        for dev in memory.get("my_developments", []) or []:
            if self.maintenance_loss_risk(dev, memory) <= 0.0:
                continue
            self._accumulate_deficits(deficits, dev.get(
                "maintenance_cost", {}) or {}, memory)
        return deficits

    def upgrade_required_resources(self, memory: Memory) -> dict[str, float]:
        deficits: dict[str, float] = {}
        for dev in memory.get("my_developments", []) or []:
            if dev.get("can_upgrade") is False:
                continue
            if not self.upgrade_marginal_output(dev, memory):
                continue
            self._accumulate_deficits(deficits, dev.get(
                "upgrade_cost", {}) or {}, memory)
        return deficits

    def owned_production_by_resource(self, memory: Memory) -> dict[str, float]:
        production: dict[str, float] = {}
        for dev in memory.get("my_developments", []) or []:
            resource = self.resource_for_type(dev.get("type"))
            if not resource:
                continue
            production[resource] = production.get(
                resource, 0.0) + self.production_per_labor(dev) * self.expected_laborers(dev, memory)
        return production

    def upgrade_opportunity_value_by_resource(self, memory: Memory) -> dict[str, float]:
        values: dict[str, float] = {}
        for dev in memory.get("my_developments", []) or []:
            for resource, value in self.upgrade_marginal_output(dev, memory).items():
                values[resource] = values.get(resource, 0.0) + value
        return values

    def at_risk_developments(self, memory: Memory) -> list[dict]:
        return [
            dev for dev in memory.get("my_developments", []) or []
            if self.maintenance_loss_risk(dev, memory) > 0.0
        ]

    def upgradable_developments(self, memory: Memory) -> list[dict]:
        return [
            dev for dev in memory.get("my_developments", []) or []
            if dev.get("can_upgrade") is not False and bool(self.upgrade_marginal_output(dev, memory))
        ]

    def workable_owned_developments(self, memory: Memory) -> list[dict]:
        my_id = memory.get("my_id")
        devs_by_id = {
            dev.get("id"): dev
            for dev in memory.get("my_developments", []) or []
            if dev.get("id")
        }
        workable = []
        for job in memory.get("available_work", []) or []:
            development = job.get("development", {}) or {}
            dev_id = development.get("id")
            owner_id = development.get("owner_id")
            if owner_id == my_id and dev_id in devs_by_id:
                workable.append(devs_by_id[dev_id])
        return workable

    def _accumulate_deficits(self, deficits: dict[str, float], cost: dict, memory: Memory) -> None:
        for resource in RESOURCE_TYPES:
            needed = float(cost.get(resource, 0) or 0)
            if needed <= 0.0:
                continue
            available = float(memory.get(resource, 0) or 0)
            deficit = max(0.0, needed - available)
            if deficit:
                deficits[resource] = deficits.get(resource, 0.0) + deficit
