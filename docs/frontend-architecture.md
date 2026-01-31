# Frontend Architecture

The frontend provides an interactive interface for planning holiday itineraries.
Users can select destinations, explore and categorize attractions, and generate
an optimized route that connects all selected locations **(POI)** in the most
efficient way.

## Table of contents

## Dependencies

## Directory Structure

The frontend code is located in the (src)[./src] directory alongside the backend
services.

```text
src/
├── streamlit_app.py             # Application entry point
├── ui/
│   ├── handlers/                # User interaction and backend coordination
│   │   ├── __init__.py
│   │   ├── add_poi.py            # Add POIs to the current itinerary
│   │   ├── delete_poi.py         # Remove POIs from the itinerary
│   │   ├── get_request.py        # HTTP requests to the backend API
│   │   ├── itinerary.py          # Itinerary-related logic and operations
│   │   ├── utils.py              # Shared helper functions for handlers
│   │   └── validators.py         # Input validation and consistency checks
│   │
│   ├── widgets/                 # UI components
│   │   ├── __init__.py
│   │   ├── controls.py           # UI controls (buttons, selectors, filters)
│   │   ├── map.py                # Map visualization and interaction
│   │   ├── poi_overview.py       # Single POI display component
│   │   ├── pois_overview.py      # Overview/list of multiple POIs
│   │   └── route.py              # Route visualization and controls
│   │
│   ├── __init__.py
│   ├── config.py                 # UI configuration and constants
│   ├── layout.py                 # Page layout and structure definition
│   ├── session_states.py         # Streamlit session state initialization
│   ├── ui.py                     # High-level UI composition
│   └── utils.py                  # Shared UI helper functions
└── ...                          # Backend services (not shown)
```
