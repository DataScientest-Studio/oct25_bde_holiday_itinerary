"""
Module to run API intended for local testing only
"""

import os

import uvicorn


def run_server():
    """
    Runs API for local testing purposes
    """
    uvicorn.run(
        "src.neo4j_api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8081")),
        reload=True,
        reload_dirs=["src/"],
        use_colors=True,
    )


if __name__ == "__main__":
    os.environ["RUNNING_UVICORN"] = "1"
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    run_server()
