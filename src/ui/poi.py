from typing import NamedTuple


class Poi(NamedTuple):
    label: str
    city: str
    description: str
    street: str
    postal_code: str
    homepage: str
    additional_information: str
    comment: str
    latitude: float
    longitude: float
    poiId: str
