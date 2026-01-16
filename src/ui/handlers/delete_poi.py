import pandas as pd
import streamlit as st
from loguru import logger

from .handlers.utils import remove_poi


class DeletePoi:
    def delete_poi(self):
        logger.debug("Deleteing POI from route DataFrame.")
        try:
            poi_id = st.session_state.selected_poi["poiId"]
            if st.session_state.route["poiId"].eq(poi_id).any():
                st.session_state.overview = self.add_poi_to_df(st.session_state.overview, st.session_state.selected_poi)
                logger.info("Added point to route POIs DataFrame.")
                st.session_state.route = self.remove_poi(st.session_state.route, poi_id)
            logger.info("Removed POI from route DataFrame.")
        except (KeyError, ValueError) as err:
            logger.error(err)

    def remove_df_from_df(self, df: pd.DataFrame, poi: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Removing df from df...")
        poi_ids = poi["poi_id"].tolist()
        for poi_id in poi_ids:
            remove_poi(df, poi_id)
        logger.info(f"Removed poiIds {poi_ids} from target.")
        return df
