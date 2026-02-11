from enum import StrEnum


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class GeographicalLocation(StrEnum):
    VILLAGE = "village"
    SMALL_TOWN = "small_town"
    MEDIUM_SIZED_TOWN = "medium_sized_town"
    LARGE_TOWN = "large_town"
    CITY = "city"
