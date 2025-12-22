from st_aggrid import AgGrid


class Grid:

    def __init__(self, df) -> None:
        self.df = df

    def run(self) -> AgGrid:
        return AgGrid(self.df)
