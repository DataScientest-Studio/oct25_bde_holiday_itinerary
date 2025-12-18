import streamlit as st


class UI:
    def __init__(self) -> None:
        # Use session, to keep data, if an other even occurs.
        # Streamlit clears the app to default back after an
        # event occurs.
        if "search" not in st.session_state:
            st.session_state.search = ""
        if "add-pois" not in st.session_state:
            st.session_state.add_pois = ""
        if "search_result" not in st.session_state:
            st.session_state.search_result = ""
        st.set_page_config(layout="wide")
        self.header()

    def header(self):
        st.title("Holiday Itinerary")

    def create_rows(self):
        col_left, col_right = st.columns([2, 3], border=True)
        self.cell_one(col_left)
        self.cell_two(col_right)

    def search_poi(self):
        search = st.session_state.search
        st.session_state.search_result = f"Searching for: {search}"

    def add_pois(self):
        pass

    def cell_one(self, cell) -> None:
        cell.header("Selected POIs")
        listing = cell.container(border=True, height=200)
        for i in range(0, 100):
            listing.write(f"Place{i}")
        col_1, _ = cell.columns([2, 3])
        if col_1.button("Plan Itinerary"):
            col_1.write("IMPLEMENT LOGIC to plan route.")

    def cell_two(self, cell) -> None:
        cell.header("Filters")
        col_1, col_2 = cell.columns([1, 1])
        col_1.multiselect("Place / City to visit", options=["Paris", "Village"], key="visit_location")
        col_1.multiselect("type of Place / City", options=["City", "Village"], key="location_type")
        col_1.multiselect("POIs", options=["Louvre", "Cafe", "Eisdiele"], key="add-pois")
        col_1.button("Add POIs", on_click=self.add_pois)
        col_2.date_input("Start", format="DD/MM/YYYY")
        col_2.date_input("End", format="DD/MM/YYYY")
        self.search_component(col_2)

    def search_component(self, cell) -> None:
        col_1, col_2 = cell.columns([2, 1])
        col_1.text_input("Search", placeholder="Type a point of interest...", key="search")
        col_2.button("Search", on_click=self.search_poi)

    def run(self):
        self.create_rows()


app = UI()
app.run()
