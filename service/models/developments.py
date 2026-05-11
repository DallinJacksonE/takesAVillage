
class Development:
    def __init__(self, dev_id, dev_type, dev_owner):
        self.id = dev_id
        self.type = dev_type
        self.level = 2
        self.owner = dev_owner
        self.maintenance_days = 7

        # --- Conflict Flags ---
        self.is_contested = False
        self.contester_id = None
        self.contester_supporters = []
        self.owner_supporters = []

    def degrade(self):
        self.maintenance_days -= 1
        if self.maintenance_days < 0:
            if self.level > 1:
                self.level -= 1
                self.maintenance_days += 7
            else:
                self.level = 1
                self.maintenance_days = 1

    def upgrade(self):
        if self.level >= 3:
            self.level = 3
            self.maintenance_days += 10
        else:
            self.level += 1
            self.maintenance_days = 7
