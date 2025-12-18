import streamlit as st


class UI:

    def __init__(self) -> None:
        # Use session, to keep data, if an other even occurs.
        # Streamlit clears the app to default back after an
        # event occurs.
        if "poi" not in st.session_state:
            st.session_state.poi = ""
        if "search_result" not in st.session_state:
            st.session_state.search_result = ""
        st.set_page_config(layout="wide")
        self.header()

    def header(self):
        st.title("Holiday Itinerary")

    def create_rows(self):
        col_left, col_right = st.columns([2, 3], border=True)
        self.cell_one(col_left)

    def search_poi(self):
        poi_query = st.session_state.poi
        st.session_state.search_result = f"Searching for: {poi_query}"

    def cell_one(self, cell) -> None:
        cell.header("POIs")
        listing = cell.container(border=True, height=200)
        for i in range(0, 100):
            listing.write(f"Place{i}")
        col_1, col_2 = cell.columns([2, 3])
        if col_1.button("Plan Itinerary"):
            col_1.write("IMPLEMENT LOGIC to plan route.")
        self.search_component(col_2)

    def search_component(self, cell) -> None:
        col_1, col_2 = cell.columns([2, 1])
        col_1.text_input("Search", placeholder="Type a point of interest...", key="poi", label_visibility="collapsed")
        col_2.button("Search", on_click=self.search_poi)

    def run(self):
        self.create_rows()


app = UI()
app.run()
