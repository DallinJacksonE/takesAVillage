
class Development:
    def __init__(self, dev_id, dev_type, dev_owner, MAX_LEVEL, MAINTENANCE_DAYS):
        self.id = dev_id
        self.type = dev_type
        self.level = 2
        self.owner = dev_owner  # the id
        self.maintenance_days = MAINTENANCE_DAYS
        self.is_contested = False
        self.contester_id = None
        self.contester_supporters = []
        self.owner_supporters = []

        self.MAX_LEVEL = MAX_LEVEL
        self.MAINTENANCE_DAYS = MAINTENANCE_DAYS

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
