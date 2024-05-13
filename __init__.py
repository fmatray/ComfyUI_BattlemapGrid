from .grid_node import BattlemapGrid
from .map_node import BattlemapMapGenerator, BattlemapMapGeneratorOutdoors
from .compass_node import CompassGrid

NODE_CLASS_MAPPINGS = {
    "Map Generator": BattlemapMapGenerator,
    "Map Generator(Outdoors)": BattlemapMapGeneratorOutdoors,
    "Compass": CompassGrid,
    "Battlemap Grid": BattlemapGrid,
}
