# Frontend Architecture

The frontend provides an interactive interface for planning holiday itineraries.
Users can select destinations, explore and categorize attractions, and generate
an optimized route that connects all selected locations **(POI)** in the most
efficient way.

## Table of contents

- [Dependencies](#dependencies)
- [Directory Structure](#directory-structure)

## Dependencies

- **[Streamlit](https://streamlit.io/)** (`1.52.2`)\
  Main UI framework and application runtime used to build the frontend.
- **[Requests](https://docs.python-requests.org/)** (`2.32.5`)\
  HTTP client used for communication with the backend API.
- **[Pandas](https://pandas.pydata.org/)** (`2.3.3`)\
  Data manipulation and transformation library used for itinerary processing.
- **[PyDeck](https://deckgl.readthedocs.io/en/latest/)** (`0.9.1`)\
  Library for map rendering and route visualization.

## Directory Structure

The frontend code is located in the [\*src/frontend](../src/frontend) directory alongside the backend
services.

```text
src/frontend
├── streamlit_app.py             # Application entry point
└── ui/
    ├── handlers/                # User interaction and backend coordination
    │   ├── __init__.py
    │   ├── add_poi.py            # Add POIs to the current itinerary
    │   ├── delete_poi.py         # Remove POIs from the itinerary
    │   ├── get_request.py        # HTTP requests to the backend API
    │   ├── itinerary.py          # Request an itinerary
    │   ├── utils.py              # Shared helper functions for handlers
    │   └── validators.py         # Input validation and consistency checks
    │
    ├── widgets/                 # UI components
    │   ├── __init__.py
    │   ├── controls.py           # UI controls/filters to select the pois
    │   ├── map.py                # Map to visualize location of pois and route
    │   ├── poi_overview.py       # Overview about a selected poi
    │   ├── pois_overview.py      # Overview of pois selected with the controls
    │   └── route.py              # Pois which are part of the itinerary
    │
    ├── __init__.py
    ├── config.py                 # UI configuration and constants
    ├── layout.py                 # Page layout and structure definition
    ├── session_states.py         # Streamlit session state initialization
    ├── ui.py                     # UI class, which is called in streamlit_app.py
    └── utils.py                  # Shared UI helper functions
```
