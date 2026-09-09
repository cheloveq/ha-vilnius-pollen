"""Constants for Vilnius Allergens."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "vilnius_allergens"
NAME: Final = "Vilnius Allergens"
MANUFACTURER: Final = "Vilnius City"
MODEL: Final = "Vilnius bioaerosol monitoring site"
LAYER_URL: Final = "https://opencity.idvilnius.lt/atviras/rest/services/Aplinka/Bioaerozoliai/MapServer/0"
UPDATE_INTERVAL: Final = timedelta(minutes=5)
POLLEN_UNIT: Final = "vnt./m³"
TIMESTAMP_FIELD: Final = "timestamp"
DATA_FIELDS: Final = ("Alnus", "Ambrosia", "Artemisia", "Betula", "Corylus", "Poaceae", "Pollen")
