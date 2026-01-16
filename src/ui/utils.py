import pandas as pd
import streamlit as st
from config import POI_COLUMNS
from loguru import logger


def init_empty_df() -> pd.DataFrame:
    df = pd.DataFrame(columns=POI_COLUMNS)
    df.fillna("", inplace=True)
    return df


def select_overview_df(key) -> None:
    df, _ = key.split("-")
    rows = st.session_state[key]["selection"]["rows"]
    if rows is not None:
        st.session_state.selected_poi = st.session_state[df].iloc[rows[0]]
        logger.debug(f"Selected row {st.session_state.selected_poi} in dataframe '{df}'")
