from typing import Any

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from logger import logger


class Grid:

    def __init__(
        self,
        df: pd.DataFrame,
        key: str,
        height: int,
        config_dict: dict[str, Any],
    ) -> None:
        logger.debug("Initalizing new grid config.")
        self.df = df
        self.key = key
        self.height = height
        self.options = self.__build_config(config_dict)
        logger.info("Initialized new grid config.")

    def __build_config(self, config: dict[str, Any]):
        logger.info("Building config.")
        if "columns" in config:
            self.__config_columns(config)

        logger.info("Builded config.")

    def __config_columns(self, config: dict[str, Any]) -> None:
        logger.debug("Configuring columns...")
        if not (columns := config.get("columns", {})):
            logger.warning("No columns to configure were found in config. Skipping function.")
            return
        self.__reorder_columns(columns)
        gb = GridOptionsBuilder.from_dataframe(self.df)
        for col, values in columns.items():
            try:
                gb.configure_column(col, **values)
                logger.debug(f"Configured column {col} with {values}.")
            except TypeError as err:
                logger.error(f"Invalid config for {col}. Error: {err}")
        logger.info("Configured columns.")
        return gb.build()

    def __reorder_columns(self, columns: dict[str, Any]) -> pd.DataFrame:
        logger.debug("Ordering columns...")
        ordered = [key for key in columns.get("columns", {}).keys()]
        self.df[ordered]
        logger.debug(f"New column order: {self.df.columns}.")
        logger.info("Ordered columns.")

    def run(self) -> AgGrid:
        logger.info("Running new grid Layout.")
        return AgGrid(
            self.df,
            gridOptions=self.options,
            key=self.key,
            height=self.height,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            show_toolbar=True,
            show_download_button=False,
        )
