"""mapgame: stylized maps of real trails from open elevation and OpenStreetMap data."""
import os
DATA = os.environ.get("MAPGAME_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
FT = 3.28084
