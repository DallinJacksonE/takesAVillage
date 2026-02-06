import random


class MapFactory:
    def __init__(self):
        self.generate_map()

    def generate_map(self, player_count):
        # 1. Determine Tile Counts
        # "Enough farm tiles... for everyone to acquire" (assuming 2 food/tile
        # vs 1 food consumption)
        # We ensure at least 1 farm per player to be safe and allow competition
        num_farms = player_count // 2

        # "Rest available for wood, then one or two for mines"
        num_woods = player_count + 1
        num_mines = 2

        tiles_to_place = ["Farm"] * num_farms + \
            ["Woods"] * num_woods + ["Mine"] * num_mines
        random.shuffle(tiles_to_place)

        # 2. Generate Hex Spiral Coordinates (q, r)
        # This creates a compact cluster of hexagons
        self.map_tiles = []
        q, r = 0, 0

        # Spiral directions for flat-topped hexes
        directions = [
            (+1, 0), (+1, -1), (0, -1),
            (-1, 0), (-1, +1), (0, +1)
        ]

        # Add center tile
        if tiles_to_place:
            self.map_tiles.append({
                "id": "t_0_0", "q": 0, "r": 0,
                "type": tiles_to_place.pop(0), "owner_id": None
            })

        # Spiral outwards
        radius = 1
        while tiles_to_place:
            # Move to start of ring (radius, 0) is not quite right for
            # hex spiral,
            # standard algo starts at q=0, r=0 then moves to neighbor 4,
            # then spirals
            q, r = -radius, radius  # Start position for ring

            for dx, dy in directions:
                for _ in range(radius):
                    if not tiles_to_place:
                        break

                    # Calculate new coord
                    q += dx
                    r += dy

                    # Add tile
                    self.map_tiles.append({
                        "id": f"t_{q}_{r}",
                        "q": q, "r": r,
                        "type": tiles_to_place.pop(0),
                        "owner_id": None
                    })
                if not tiles_to_place:
                    break
            radius += 1
