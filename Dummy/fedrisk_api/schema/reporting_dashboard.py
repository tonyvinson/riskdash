from pydantic import BaseModel


class CreateReportingSettings(BaseModel):
    user_id: str
    column_state: str = None
    pivot_state: bool = None
    graph_state: str = None
    # selected_row_state: str = None
    value_columns: str = None
    grid_cols: str = None
    # chart_models: str = None
    # col_def_user: str = None
    # saved_cell_ranges: str = None
    # grid_state: str = None


class UpdateReportingSettings(BaseModel):
    user_id: str
    column_state: str = None
    pivot_state: bool = None
    graph_state: str = None
    # selected_row_state: str = None
    value_columns: str = None
    grid_cols: str = None
    # chart_models: str = None
    # col_def_user: str = None
    # saved_cell_ranges: str = None
    # grid_state: str = None

    class Config:
        orm_mode = True


class DisplayReportingSettings(BaseModel):
    id: str = None
    user_id: str = None
    column_state: str = None
    pivot_state: bool = None
    graph_state: str = None
    # selected_row_state: str = None
    value_columns: str = None
    grid_cols: str = None
    # chart_models: str = None
    # col_def_user: str = None
    # saved_cell_ranges: str = None
    # grid_state: str = None

    class Config:
        orm_mode = True
