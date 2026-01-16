import pandas as pd
import pydeck as pdk
import streamlit as st

from logger import logger


class Map:

    def __init__(self) -> None:
        logger.debug("Initializing Map...")

        df_cities = pd.DataFrame(st.session_state.cities)

        center_lat, center_lon, zoom = self.center_map(df_cities)
        if st.session_state.selected_poi is None:
            layers = [self.create_route_points()]
        else:
            layers = [self.create_selected_poi(), self.create_route_points()]

        if not st.session_state.ordered_route.empty:
            layers.extend(self.create_route_edges())

        r = pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, height=734),
            map_style="road",
            tooltip=None,
        )

        st.pydeck_chart(r, height=734)

        logger.info("Initalized Map.")

    def create_selected_poi(self) -> pdk.Layer:
        color = [255, 0, 0] if st.session_state.selected_poi["poiId"] in st.session_state.route else [0, 0, 255]
        df = pd.DataFrame([st.session_state.selected_poi])
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        return pdk.Layer(
            "ScatterplotLayer",
            id="selected-poi",
            data=df,
            get_position=["longitude", "latitude"],
            radius_units="pixels",
            radius_min_pixels=3,
            radius_max_pixels=3,
            get_color=color,
            pickable=True,
        )

    def create_route_points(self) -> tuple[pdk.Layer, ...]:
        pois = st.session_state.route
        if not st.session_state.ordered_route.empty:
            start_poi = st.session_state.ordered_route.iloc[0]["poiId"]
            pois = st.session_state.route[st.session_state.route["poiId"] != start_poi].reset_index(drop=True)
            end_poi = st.session_state.ordered_route.iloc[0]["poiId"]
            pois = pois[pois["poiId"] != end_poi].reset_index(drop=True)
        return pdk.Layer(
            "ScatterplotLayer",
            id="route",
            data=pois,
            get_position=["longitude", "latitude"],
            radius_units="pixels",
            radius_min_pixels=3,
            radius_max_pixels=3,
            get_color=[255, 0, 0],
            pickable=True,
        )

    def create_route_edges(self) -> pdk.Layer:
        path_coords = st.session_state.ordered_route[["longitude", "latitude"]].values.tolist()
        logger.warning(path_coords)
        route = pdk.Layer(
            "PathLayer",
            id="route-edges",
            data=pd.DataFrame({"path": [path_coords]}),
            get_path="path",
            get_color=[0, 0, 0],
            width_min_pixels=1,
        )
        start = pdk.Layer(
            "ScatterplotLayer",
            id="start-node",
            data=st.session_state.ordered_route.iloc[:1],
            get_position=["longitude", "latitude"],
            radius_units="pixels",
            radius_min_pixels=3,
            radius_max_pixels=3,
            get_color=[0, 255, 0],
            pickable=True,
        )
        end = pdk.Layer(
            "ScatterplotLayer",
            id="end-node",
            data=st.session_state.ordered_route.iloc[-1:],
            get_position=["longitude", "latitude"],
            radius_units="pixels",
            radius_min_pixels=3,
            radius_max_pixels=3,
            get_color=[255, 0, 255],
            pickable=True,
        )

        return route, start, end

    def center_map(self, data_pois: pd.DataFrame) -> tuple[float, float, int]:
        dfs = []
        if st.session_state.selected_poi is not None and not st.session_state.selected_poi.empty:
            dfs.append(
                pd.DataFrame(
                    {
                        "longitude": [float(st.session_state.selected_poi["longitude"])],
                        "latitude": [float(st.session_state.selected_poi["latitude"])],
                    }
                ),
            )
        if not st.session_state.route.empty:
            dfs.append(st.session_state.route[["latitude", "longitude"]])
        if dfs:
            data_pois = pd.concat(dfs)
        min_lat, max_lat = data_pois["latitude"].min(), data_pois["latitude"].max()
        min_lon, max_lon = data_pois["longitude"].min(), data_pois["longitude"].max()
        lat = (min_lat + max_lat) / 2
        lon = (min_lon + max_lon) / 2
        return lat, lon, self.calculate_zoom(min_lat, max_lat, min_lon, max_lon)

    def calculate_zoom(self, min_lat, max_lat, min_lon, max_lon):
        # https://wiki.openstreetmap.org/wiki/Zoom_levels
        lat_span = abs(max_lat - min_lat)
        lon_span = abs(max_lon - min_lon)

        if lat_span == 0 and lon_span == 0:
            return 12

        max_span = max(lat_span, lon_span)
        if max_span < 0.00034:
            return 20
        elif max_span < 0.00069:
            return 19
        elif max_span < 0.0014:
            return 18
        elif max_span < 0.0027:
            return 17
        elif max_span < 0.0055:
            return 16
        elif max_span < 0.011:
            return 15
        elif max_span < 0.022:
            return 14
        elif max_span < 0.044:
            return 13
        elif max_span < 0.088:
            return 12
        elif max_span < 0.176:
            return 11
        elif max_span < 0.352:
            return 10
        elif max_span < 0.703:
            return 9
        elif max_span < 1.406:
            return 8
        elif max_span < 2.813:
            return 7
        elif max_span < 5.625:
            return 6
        elif max_span < 11.25:
            return 5
        elif max_span < 22.5:
            return 5  # Fixed zoom for france.
        elif max_span < 45:
            return 3
        elif max_span < 90:
            return 2
        elif max_span < 180:
            return 1
        else:
            return 0
