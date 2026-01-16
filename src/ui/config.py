import pandas as pd

POI_COLUMNS: list[str] = [
    "label",
    "city",
    "description",
    "street",
    "postal_code",
    "homepage",
    "additional_information",
    "comment",
    "latitude",
    "longitude",
    "poiId",
]


def init_empty_df() -> pd.DataFrame:
    df = pd.DataFrame(columns=POI_COLUMNS)
    df.fillna("", inplace=True)
    return df
