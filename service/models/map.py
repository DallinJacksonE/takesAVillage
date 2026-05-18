import random


class MapTile:
    def __init__(self,
                 tile_id: str,
                 q: int,
                 r: int,
                 tile_type: str,
                 ):

        self.id = tile_id
        self.q = q
        self.r = r
        self.type = tile_type
        self.owner_id = ""
        self.development = None


class MapFactory:
    def __init__(self, player_count, farms_ratio, woods_ratio, mountains_ratio):
        self.map_tiles = {}
        self.generate_map(player_count, farms_ratio,
                          woods_ratio, mountains_ratio)

    def generate_map(self, player_count, farms_ratio, woods_ratio, mountains_ratio):
        # 1. Determine Tile Counts
        num_farms = max(int(player_count * farms_ratio), 1)
        num_woods = max(int(player_count * woods_ratio), 1)
        num_mines = max(int(player_count * mountains_ratio), 1)

        tiles_to_place = ["Farm"] * num_farms + \
            ["Woods"] * num_woods + ["Mine"] * num_mines
        random.shuffle(tiles_to_place)

        # 2. Generate Hex Spiral Coordinates (q, r)
        self.map_tiles = {}
        q, r = 0, 0

        # Spiral directions for flat-topped hexes
        directions = [
            (+1, 0), (+1, -1), (0, -1),
            (-1, 0), (-1, +1), (0, +1)
        ]

        def addtile(map_tiles, new_tile):
            map_tiles.update({new_tile.id: new_tile})

        # Add center tile
        if tiles_to_place:
            addtile(self.map_tiles,
                    MapTile(tile_id="t_0_0", q=0, r=0,
                            tile_type=tiles_to_place.pop(0)))

        # Spiral outwards
        radius = 1
        while tiles_to_place:
            q, r = -radius, radius  # Start position for ring

            for dx, dy in directions:
                for _ in range(radius):
                    if not tiles_to_place:
                        break

                    # Calculate new coord
                    q += dx
                    r += dy

                    # Add tile
                    addtile(self.map_tiles,
                            MapTile(tile_id=f"t_{q}_{r}", q=q, r=r,
                                    tile_type=tiles_to_place.pop(0))
                            )
                if not tiles_to_place:
                    break
            radius += 1
