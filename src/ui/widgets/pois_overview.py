import pandas as pd
import streamlit as st
from config import POI_COLUMNS
from handler import handle_get_request
from loguru import logger
from utils import init_empty_df, select_overview_df


class PoisOverview:
    def __init__(self) -> None:
        logger.debug("Initializing pois overview...")
        if st.session_state.destinations or st.session_state.categories:
            params = {
                "locations": st.session_state.destinations or "",
                "types": st.session_state.categories or "",
                "radius": st.session_state.radius * 1000,
            }
            if params != st.session_state.old_params:
                try:
                    pois = handle_get_request("/poi/filter", params).get("pois", {})
                    st.session_state.overview = pd.DataFrame(pois, columns=POI_COLUMNS) if pois else init_empty_df()
                    st.session_state.overview.fillna("", inplace=True)
                    st.session_state.old_params = params
                    logger.info("Initalized poi overview.")
                except Exception:
                    logger.error("Failed to get '/poi/filter' form the server.")

        key = "overview-pois"
        _ = st.dataframe(
            st.session_state.overview,
            key=key,
            height=500,
            hide_index=True,
            column_order=["label", "city", "description"],
            column_config={
                "label": st.column_config.TextColumn(
                    "POI",
                    width=100,
                    help="The label of the POI.",
                ),
                "city": st.column_config.TextColumn(
                    "Location",
                    width=100,
                    help="Location of the POI.",
                ),
                "description": st.column_config.TextColumn(
                    "Description",
                    help="Description of the POI.",
                ),
            },
            on_select=lambda: select_overview_df(key),
            selection_mode="single-row",
            placeholder="-",
        )
