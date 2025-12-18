import streamlit as st


class UI:

    def __init__(self) -> None:
        st.set_page_config(layout="wide")
        self.header()

    def header(self):
        st.title("Holiday Itinerary")

    def create_rows(self):
        self.first_row()
        self.second_row()

    def first_row(self):
        col_left, col_right = st.columns([1, 3])
        with col_left:
            st.title("POIs")

        with col_right:
            st.title("Filter")

    def second_row(self):
        col_left, col_right = st.columns([3, 1])
        with col_left:
            st.title("Map")

        with col_right:
            st.title("Sidebar")

    def run(self):
        self.create_rows()


app = UI()
app.run()
