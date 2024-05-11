from .grid_node import BattlemapGrid
from .map_node import BattlemapMapGenerator, BattlemapMapGeneratorOutdoors

NODE_CLASS_MAPPINGS = {
    "Battlemap Grid": BattlemapGrid,
    "Map Generator": BattlemapMapGenerator,
    "Map Generator(Outdoors)": BattlemapMapGeneratorOutdoors,
}
