"""Constants for Vilnius Allergens."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "vilnius_allergens"
NAME: Final = "Vilnius Allergens"
MANUFACTURER: Final = "Vilnius City"
MODEL: Final = "Vilnius bioaerosol monitoring site"
LAYER_URL: Final = "https://opencity.idvilnius.lt/atviras/rest/services/Aplinka/Bioaerozoliai/MapServer/0"
UPDATE_INTERVAL: Final = timedelta(minutes=5)
MAX_MEASUREMENT_AGE: Final = timedelta(hours=3)
POLLEN_UNIT: Final = "vnt./m³"
TIMESTAMP_FIELD: Final = "timestamp"
DATA_FIELDS: Final = ("Alnus", "Ambrosia", "Artemisia", "Betula", "Corylus", "Poaceae")
RISK_OPTIONS: Final = ("low", "medium", "high", "very_high")
SOURCE_RISK_LIMITS: Final = {
    "Alnus": (55, 116, 170),
    "Corylus": (5, 16, 20),
    "Betula": (70, 151, 215),
    "Poaceae": (10, 21, 35),
    "Artemisia": (15, 31, 50),
    "Ambrosia": (4, 6, 10),
}
SERVICE_QUERY_HISTORY: Final = "query_history"
MAX_HISTORY_RECORDS: Final = 2_000
