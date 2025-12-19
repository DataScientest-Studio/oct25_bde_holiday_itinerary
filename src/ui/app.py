import logging
from json import loads
from typing import Any

import streamlit as st
from requests import get
from requests.models import HTTPError

LOG = logging.Logger("ui-logger")


def handle_get_request(target: str, query_params: dict[str, str] | None = None) -> dict[str, Any]:
    response = get(f"http://neo4j_api:8080{target}", params=query_params)
    if response.status_code == 200:
        return loads(response.text)
    raise HTTPError(f"Status code is not 200. Received: {response.status_code}")


class UI:
    def __init__(self) -> None:
        if "locations" not in st.session_state:
            st.session_state.locations = []
        if "filter_type" not in st.session_state:
            st.session_state.filter_type = []
        if "filtered-pois" not in st.session_state:
            st.session_state.filtered_pois = {}
        if "selected_pois" not in st.session_state:
            st.session_state.selected_pois = []

        self.header()

    def header(self):
        st.set_page_config(page_title="Holiday Itinerary", layout="wide")
        st.title("Holiday Itinerary")

    def create_rows(self):
        self.create_top_row()
        self.create_bottom_row()

    def create_top_row(self):
        selected_pois_col, filters_col = st.columns([5, 2], border=True)
        self.create_selected_pois_col(selected_pois_col)
        self.create_filters_col(filters_col)

    def create_selected_pois_col(self, cell) -> None:
        cell.header("Selected POIs")
        selected_pois_list = cell.container(border=True, height=220)
        for poi in st.session_state.selected_pois:
            selected_pois_list.write(poi)
        button_col, _ = cell.columns([2, 3])
        if button_col.button("Plan Itinerary"):
            button_col.write("IMPLEMENT LOGIC to plan route.")

    def create_filters_col(self, cell) -> None:
        cell.header("Filters")
        poi_filters, date_filters = cell.columns([1, 1])
        poi_filters.multiselect("Place / City to visit", options=self.get_locations(), key="locations")
        poi_filters.multiselect("Type of Place / City", options=self.select_types(), key="filter_type")
        poi_filters.multiselect("POIs", options=self.get_filtered_pois(), key="selected_pois")
        date_filters.date_input("Start", format="DD/MM/YYYY")
        date_filters.date_input("End", format="DD/MM/YYYY")

    def get_locations(self) -> list[str]:
        try:
            return handle_get_request("/city/")["cities"]
        except Exception:
            return st.session_state.locations if st.session_state.locations else [""]

    def select_types(self) -> list[str]:
        try:
            return handle_get_request("/poi/types/")["types"]
        except Exception:
            return st.session_state.filter_type if st.session_state.filter_type else [""]

    def get_filtered_pois(self) -> list[str]:
        if not st.session_state.locations and not st.session_state.filter_type:
            return []
        params = {
            "locations": ",".join(st.session_state.locations) or "",
            "types": ",".join(st.session_state.filter_type) or "",
        }
        try:
            pois = handle_get_request("/poi/filter", params)
            st.session_state.filtered_pois = pois.get("pois", [])
            return [poi["label"] for poi in pois.get("pois", [])]
        except Exception as e:
            LOG.error(f"Failed to fetch POIs: {e}")
            return []

    def add_pois(self):
        pass

    def create_bottom_row(self) -> None:
        map_col, route_col = st.columns([5, 2], border=True)
        self.create_route_col(route_col)

    def create_route_col(self, cell) -> None:
        cell.header("Created Route")
        route_pois_list = cell.container(border=True, height=500)
        for poi in st.session_state.selected_pois:
            route_pois_list.write(poi)

    def run(self) -> None:
        self.create_rows()


app = UI()
app.run()
