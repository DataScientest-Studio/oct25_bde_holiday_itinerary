### Project Architecture

The following diagram illustrates the overall architecture of the project, including the data flow and the relationships between the different services.

```mermaid
%%| fig-align: center
%%| fig-height: 80%
%%{init: {'theme': 'neutral', 'themeVariables': { 'primaryColor': '#e3f2fd', 'primaryTextColor': '#1565c0', 'primaryBorderColor': '#90caf9', 'lineColor': '#b0bec5', 'secondaryColor': '#fff9c4', 'tertiaryColor': '#f1f8e9', 'mainBkg': '#fafafa', 'nodeBorder': '#90caf9', 'clusterBkg': '#ffffff', 'clusterBorder': '#cfd8dc', 'edgeColor': '#90a4ae'}}}%%
graph LR
    subgraph " "
        direction TB

        subgraph Client Layer
            UI[Streamlit UI]
        end

        subgraph API Layer
            Backend[FastAPI Backend]
        end

        subgraph Database Layer
            Neo4j[(Neo4j Database)]
        end

        subgraph Orchestration Layer
            Airflow[Apache Airflow]
        end
    end

    subgraph External
        DataTourisme[DataTourisme API/Feed]
    end

    UI -->|REST API| Backend
    Backend -->|Bolt Protocol| Neo4j
    Airflow -->|Trigger ETL via REST| Backend
    Backend -->|Download/Extract| DataTourisme
    Backend -->|Import Data| Neo4j

%% Storage
    subgraph Storage
        Files[(Local Files / Volumes)]
    end

    Backend -.-> Files
    Neo4j -.-> Files
    Airflow -.-> Files
```

### Components Description

- **Streamlit UI**: Provides a user-friendly interface for holiday itinerary planning. It consumes data and services provided by the FastAPI Backend.
- **FastAPI Backend**: Acts as the central hub of the application. It handles business logic, provides RESTful endpoints for the UI, and manages ETL processes.
- **Neo4j Database**: Stores the graph data, including Points of Interest (POIs), Cities, and their relationships (IS_IN, ROAD_TO, etc.).
- **Apache Airflow**: Orchestrates the data ingestion and processing pipeline. It periodically triggers the Backend to download and import new data from DataTourisme.
- **DataTourisme**: The external data source providing tourism-related information.
### Data Upload Process

The following flow chart describes the orchestrated data upload process managed by Airflow.

```mermaid
%%| fig-align: center
%%{init: {'theme': 'neutral', 'themeVariables': { 'primaryColor': '#e3f2fd', 'primaryTextColor': '#1565c0', 'primaryBorderColor': '#90caf9', 'lineColor': '#b0bec5', 'secondaryColor': '#fff9c4', 'tertiaryColor': '#f1f8e9', 'mainBkg': '#fafafa', 'nodeBorder': '#90caf9', 'clusterBkg': '#ffffff', 'clusterBorder': '#cfd8dc', 'edgeColor': '#90a4ae'}}}%%
graph LR
    subgraph "DAG flow"
        Start([Start DAG]) --> Download[Download Data]
        Download --> Unzip[Unzip Archive]
        Unzip --> Extract[Extract & Process]
        Extract --> Import[Import to Neo4j]
        Import --> Cleanup[Cleanup Temp Files]
        Cleanup --> End([End DAG])
    end    

    subgraph "Each Step Includes"
        Trigger[Trigger Backend Task] --> Poll{Wait for Completion}
        Poll -- No --> Poll
        Poll -- Yes --> Next[Next Step]
    end
```
