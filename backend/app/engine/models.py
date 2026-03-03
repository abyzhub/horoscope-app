from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class PlanetName(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"
    ASCENDANT = "Ascendant"

class ZodiacSign(str, Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"

class PlanetPosition(BaseModel):
    name: PlanetName
    longitude: float # 0 to 360 sidereal degrees
    sign: ZodiacSign
    sign_degree: float # 0 to 30 degrees within the sign
    house: int # 1 to 12
    nakshatra: str
    nakshatra_pada: int # 1 to 4
    is_retrograde: bool

class ChartData(BaseModel):
    ascendant: PlanetPosition
    planets: List[PlanetPosition]
