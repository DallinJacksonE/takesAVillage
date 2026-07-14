
class Development:
    def __init__(self, dev_id, dev_type, dev_owner, MAX_LEVEL, MAINTENANCE_DAYS, RESOURCE_COSTS):
        self.id = dev_id
        self.type = dev_type
        self.level = 2
        self.owner = dev_owner  # the id
        self.maintenance_days = MAINTENANCE_DAYS
        self.is_contested = False
        self.contest_initiator_id = None
        self.contester_supporters = []
        self.owner_supporters = []
        self.pending_contest = False
        self.pending_contest_day = None
        self.RESOURCE_COSTS = RESOURCE_COSTS

        self.MAX_LEVEL = MAX_LEVEL
        self.MAINTENANCE_DAYS = MAINTENANCE_DAYS

    @property
    def can_upgrade(self):
        return self.level < self.MAX_LEVEL

    def get_upgrade_cost(self):
        if self.type not in self.RESOURCE_COSTS:
            return {
                "food": self.level,
                "wood": self.level,
                "iron": self.level * 2 + 1
            }
        opposite = self.RESOURCE_COSTS[self.type]
        return {
            opposite: self.level * 2 + 1,
            "iron": self.level
        }

    def get_maintenance_cost(self):
        if self.type not in self.RESOURCE_COSTS:
            return {
                "food": self.level * 2 + 1,
                "wood": self.level * 2 + 1
            }
        opposite = self.RESOURCE_COSTS[self.type]
        return {
            opposite: self.level,
            "iron": max(self.level - 1, 0)
        }

    def degrade(self):
        self.maintenance_days -= 1
        if self.maintenance_days < 0 and self.level == 0:
            return False
        if self.maintenance_days < 0:
            if self.level > 1:
                self.level -= 1
                self.maintenance_days += self.MAINTENANCE_DAYS
            else:
                self.level = 1
                self.maintenance_days = 1
        return True

    def maintenance(self):
        self.maintenance_days = self.MAINTENANCE_DAYS

    def upgrade(self):
        if self.level >= self.MAX_LEVEL:
            self.level = self.MAX_LEVEL
            self.maintenance_days += self.MAINTENANCE_DAYS
        else:
            self.level += 1
            self.maintenance_days = self.MAINTENANCE_DAYS

    def to_dict(self) -> dict:
        """
        Serializes the DTO into a standard Python dictionary for JSON conversion.
        Should match DevelopmentDTO in index.ts
        """
        return {
            "id": self.id,
            "type": self.type,
            "level": self.level,
            "maintenance_days": self.maintenance_days,
            "owner_id": self.owner,
            "is_contested": self.is_contested,
            "contest_initiator_id": self.contest_initiator_id,
            "contester_supporters": self.contester_supporters,
            "owner_supporters": self.owner_supporters,
            "maintenance_cost": self.get_maintenance_cost(),
            "upgrade_cost": self.get_upgrade_cost(),
            "can_upgrade": self.can_upgrade,
            "pending_contest": self.pending_contest
        }


"""export interface DevelopmentDTO {
  id: string;
  type: "Farm" | "Woods" | "Mine";
  level: number;
  maintenance_days: number;
  owner_id: string;
  is_contested?: boolean;
  contest_initiator_id?: string;
  contester_supporters?: string[];
  owner_supporters?: string[];
}"""
