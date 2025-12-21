from datetime import date
from json import loads
from typing import Any, NamedTuple

import pandas as pd
import streamlit as st
from requests import get
from requests.models import HTTPError
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from logger import logger


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


def handle_get_request(target: str, query_params: dict[str, str] | None = None) -> dict[str, Any]:
    logger.info(f"Sending GET request to http://neo4j_api:8080{target} with params: {query_params}")
    try:
        response = get(f"http://neo4j_api:8080{target}", params=query_params)
        logger.debug(f"Received response returned status code {response.status_code}")

        match response.status_code:
            case 200:
                logger.success(f"GET request to http://neo4j_api:8080{target} succeeded")
                return loads(response.text)
            case _:
                logger.warning(f"GET request to {target} returned {response.status_code}")
                raise HTTPError(f"Request did not return 200. It returned {response.status_code}.")
    except Exception as err:
        logger.error(f"GET request to http://neo4j_api:8080{target} failed: {err}")
        raise


class UI:
    title_name: str = "Holiday Itinerary"
    layout: str = "wide"
    poi_cols: list[str] = [
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
    visible_columns: list[str] = [
        "label",
        "city",
        # "street",
        # "postal_code",
        # "homepage",
        "description",
    ]
    old_params: dict[str, Any] = {}

    def __init__(self) -> None:
        logger.debug("Initializing UI for holiday itinerary...")

        st.set_page_config(page_title=self.title_name, layout=self.layout)
        logger.debug(f"Set page title to '{self.title_name}' and layout style to '{self.layout}'.")

        st.title(self.title_name)
        logger.debug(f"Set title to '{self.title_name}'.")

        self.__init_session_states()
        self.__init_layout()

        logger.success("Initialized UI.")

    def __init_session_states(self) -> None:
        logger.debug("Initializing session states...")
        keys = ["destinations", "categories", "pois", "selected_rows", "route_pois"]
        values = [[], [], self.init_empty_pois_dataframe(), None, self.init_empty_pois_dataframe()]
        for key, value in zip(keys, values):
            if not hasattr(st.session_state, key):
                setattr(st.session_state, key, value)
                logger.debug(f"Set {key} to: {getattr(st.session_state, key)}.")
            else:
                logger.debug(f"Load previous {key}: {getattr(st.session_state, key)}.")

        logger.success("Initialized session_states.")

    def init_empty_pois_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(columns=self.poi_cols)
        df.fillna("", inplace=True)
        return df

    def __init_layout(self) -> None:
        logger.debug("Initializing layout...")
        overview, poi_view = st.columns([7, 3], border=True)
        logger.debug("Created columns for controls and poi overview.")
        with overview:
            controls, pois_overview = st.columns([3, 7])
            with controls as _:
                self.__init_controls()
            with pois_overview as _:
                self.__init_pois_overview_layout()
        with poi_view:
            self.__init_poi_overview_layout()
        logger.info("Initalized layout.")

    def __init_poi_overview_layout(self) -> None:
        logger.debug("Initializing pois overview...")
        if not st.session_state.selected_rows:
            st.subheader("POI Overview")
            logger.info("Initialized empty poi overview.")
            return
        poi: Poi = st.session_state.selected_rows
        st.title(poi.label)
        st.caption(f"📍 {poi.street}, {poi.postal_code} {poi.city}")
        st.markdown("### Description")
        st.markdown("ℹ️ **Description**")
        st.write(poi.description if poi.description else "Point of interest has no description.")
        if poi.additional_information:
            st.markdown("ℹ️ **Additional Information**")
            st.write(poi.additional_information)
        st.markdown(f"**Website**: [🌐 Visit website]({poi.homepage})")
        # st.markdown("### 🗺️ Location")
        # st.map(
        #     [
        #         {
        #             "lat": poi.latitude,
        #             "lon": poi.longitude,
        #         }
        #     ]
        # )
        logger.info("Initalized pois overview.")

    def __init_controls(self) -> None:
        logger.debug("Initializing controls...")
        st.subheader("Filter")
        with st.container():
            self.__init_filter("destinations", "/city/all", "cities", "Itinerary Destinations")
        with st.container():
            self.__init_filter("categories", "/poi/types", "types", "Category of POIs")
        with st.container():
            self.__init_date_selector("start")
        with st.container():
            self.__init_date_selector("end")

        logger.info("Initalized controls.")

    def __init_filter(self, key: str, path: str, data_key: str, label: str) -> None:
        logger.debug(f"Initializing {key} filter...")
        try:
            destinations = handle_get_request(path)[data_key]
            st.multiselect(label, options=destinations, key=key)
            logger.info(f"Initalized {key} filter.")
        except Exception as err:
            logger.error(f"Failed to get '{key}' form the server. Error: {err}")

    def __init_date_selector(self, name: str) -> None:
        logger.debug(f"Initializing {name} selector...")
        st.date_input(f"Itinerary {name}", value=date.today(), format="DD/MM/YYYY", key=name)
        logger.info(f"Initalized {name} selector.")

    def __init_pois_overview_layout(self) -> None:
        logger.debug("Initializing pois overview...")
        if st.session_state.destinations or st.session_state.categories:
            params = {
                "locations": st.session_state.destinations or "",
                "types": st.session_state.categories or "",
            }
            if not params == self.old_params:
                try:
                    pois = handle_get_request("/poi/filter", params).get("pois", {})
                    st.session_state.pois = (
                        pd.DataFrame(pois, columns=self.poi_cols) if pois else self.init_empty_pois_dataframe()
                    )
                    st.session_state.pois.fillna("", inplace=True)
                    self.old_params = params
                    logger.info("Initalized poi overview.")
                except Exception:
                    logger.error("Failed to get '/poi/filter' form the server.")
        df, options = self._config_grid()
        logger.debug("Initializing AgGrid.")

        grid_response = AgGrid(
            df,
            gridOptions=options,
            key="poisId",
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            show_toolbar=True,
            show_download_button=False,
        )
        self._get_selected_poi(grid_response.selected_rows)

    def _get_selected_poi(self, selected_rows: pd.DataFrame | None) -> None:
        logger.debug("Store selected nodes.")
        if not isinstance(selected_rows, pd.DataFrame):
            logger.debug("Not a vailid DataFrame. Can not store selected rows.")
            return
        for i, row in selected_rows.iterrows():
            poi = Poi(*row.tolist())
            st.session_state.selected_rows = poi
            logger.debug(f"Added row {i}: {poi}")
        logger.info("Added selected pois to selected rows.")

    def _config_grid(self) -> tuple[pd.DataFrame, GridOptionsBuilder]:
        logger.debug("Configure the poi overview...")
        try:
            df = self._reorder_columns(st.session_state.pois)
            gb = GridOptionsBuilder.from_dataframe(df)
            self._select_visible_columns(gb)
            gb.configure_selection("single", use_checkbox=True)
            gb.configure_column("label", maxWidth=150, headerName="POI")
            gb.configure_column("city", maxWidth=150, headerName="City")
            gb.configure_column("description", headerName="Description")
            gb.configure_default_column(resizable=True, autoSize=True)

            logger.info("Configured poi overview.")
            return df, gb.build()
        except Exception as err:
            logger.error(f"Can not configure poi grid. Error {err}")
            raise

    def _reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Sorting columns...")
        ordered_cols = [col for col in self.visible_columns if col in df.columns]
        extra_cols = [col for col in df.columns if col not in ordered_cols]
        logger.info("Sorted columns.")
        return df[ordered_cols + extra_cols]

    def _select_visible_columns(self, gb: GridOptionsBuilder) -> None:
        logger.debug("Configure visible columns...")
        for col in st.session_state.pois.columns:
            if col not in self.visible_columns:
                gb.configure_column(col, hide=True)
        logger.info("Configured visible columns.")

    def _get_ilocs_of_existing_row_in_df(self, df: pd.DataFrame) -> list[int]:
        logger.debug("Getting index of already selected values in dataframe.")
        selected_ids = [row[self.poi_cols.index("poiId")] for row in st.session_state.selected_rows]
        indices = df.index[df["poiId"].isin(selected_ids)].tolist()
        logger.debug(f"Indices to pre-select: {indices}.")
        logger.info("Calculate index of rows to preselect.")
        return indices

    def run(self) -> None:
        logger.info("Starting UI.")


app = UI()
app.run()
