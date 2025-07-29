from pydantic import BaseModel


class CreateFeature(BaseModel):
    name: str
    is_active: bool


class UpdateFeature(BaseModel):
    name: str = None
    is_active: bool = None

    class Config:
        orm_mode = True


class DisplayFeature(BaseModel):
    id: str
    name: str
    is_active: bool

    class Config:
        orm_mode = True


class CreateFeatureProject(BaseModel):
    feature_id: str
    project_id: str
    is_active: bool


class UpdateFeatureProject(BaseModel):
    feature_id: str = None
    project_id: str = None
    is_active: bool = None

    class Config:
        orm_mode = True


class DisplayFeatureProject(BaseModel):
    id: str = None
    feature_id: str = None
    project_id: str = None
    is_active: bool = None
    feature: DisplayFeature = None

    class Config:
        orm_mode = True
