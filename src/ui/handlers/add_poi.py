import pandas as pd
import streamlit as st
from loguru import logger

from .handlers.utils import remove_poi
from .handlers.validators import has_attr, is_column


class AddPoi:
    def add_poi(self) -> None:
        logger.debug("Adding POI to route DataFrame.")
        try:
            st.session_state.route = self.add_poi_to_df(
                st.session_state.route,
                st.session_state.selected_poi,
            )
            logger.info("Added point to route POIs DataFrame.")
            st.session_state.overview = remove_poi(
                st.session_state.overview,
                st.session_state.selected_poi.poiId,
            )
            logger.info("Removed POI from pois DataFrame.")
        except (KeyError, ValueError) as err:
            logger.error(err)

    def add_poi_to_df(self, df: pd.DataFrame, poi: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Handle add point to dataframe.")

        is_column("poiId", df)
        has_attr("poiId", poi)

        if poi["poiId"] in df["poiId"].values:
            logger.debug("poiId already in dest.")
            raise ValueError(f"Row with poiId {poi.poiId} already dataframe..")

        df.loc[len(df)] = {col: getattr(poi, col, None) for col in df.columns}
        logger.info("Added point to dataframe.")

        return df
