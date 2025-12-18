import streamlit as st


class UI:
    def __init__(self) -> None:
        # Use session, to keep data, if an other even occurs.
        # Streamlit clears the app to default back after an
        # event occurs.
        if "search_result" not in st.session_state:
            st.session_state.search_result = ""
        self.set_session_states()

        self.header()

    def set_session_states(self) -> None:
        if "filter-location" not in st.session_state:
            st.session_state.filter_location = ""
        if "filter-type" not in st.session_state:
            st.session_state.filter_type = ""
        if "select-pois" not in st.session_state:
            st.session_state.select_pois = ""
        if "add-pois" not in st.session_state:
            st.session_state.add_pois = ""

    def header(self):
        title = "Holiday Itinerary"
        st.set_page_config(page_title=title, layout="wide")
        st.title(title)

    def create_rows(self):
        self.create_top_row()
        self.create_bottom_row()

    def create_top_row(self):
        selected_pois_col, filters_col = st.columns([2, 5], border=True)
        self.create_selected_pois_col(selected_pois_col)
        self.create_filters_col(filters_col)

    def create_selected_pois_col(self, cell) -> None:
        cell.header("Selected POIs")
        selected_pois_list = cell.container(border=True, height=220)
        for i in range(0, 100):
            selected_pois_list.write(f"Place{i}")
        button_col, _ = cell.columns([2, 3])
        if button_col.button("Plan Itinerary"):
            button_col.write("IMPLEMENT LOGIC to plan route.")

    def create_filters_col(self, cell) -> None:
        cell.header("Filters")
        poi_filters, date_filters = cell.columns([1, 1])
        poi_filters.multiselect("Place / City to visit", options=self.select_locations(), key="filter-location")
        poi_filters.multiselect("Type of Place / City", options=self.select_types(), key="filter-type")
        poi_filters.multiselect("POIs", options=self.select_pois(), key="select-pois")
        poi_filters.button("Add POIs", on_click=self.add_pois(), key="add-pois")
        date_filters.date_input("Start", format="DD/MM/YYYY")
        date_filters.date_input("End", format="DD/MM/YYYY")
        # self.search_component(col_2)

    def select_locations(self) -> list[str]:
        return ["Paris", "Village"]

    def select_types(self) -> list[str]:
        return ["City", "Village"]

    def select_pois(self) -> list[str]:
        return ["Louvre", "Cafe", "Eisdiele"]

    def add_pois(self):
        pass

    def create_bottom_row(self) -> None:
        map_col, route_col = st.columns([5, 2], border=True)
        self.create_route_col(route_col)

    def create_map_col(self, cell) -> None:
        pass

    def create_route_col(self, cell) -> None:
        cell.header("Created Route")
        route_pois_list = cell.container(border=True, height=500)
        for i in range(0, 100):
            route_pois_list.write(f"Place{i}")

    def run(self) -> None:
        self.create_rows()


app = UI()
app.run()
