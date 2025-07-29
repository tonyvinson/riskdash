from typing import List

from pydantic import BaseModel
from fedrisk_api.schema.cost import DisplayCost
from typing import Optional


class DisplayKeyword(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayKeywordID(BaseModel):
    id: str = None
    keyword: DisplayKeyword = None

    class Config:
        orm_mode = True


class CreateWBS(BaseModel):
    name: str
    description: str = None
    project_id: str
    user_id: str

    class Config:
        orm_mode = True


class UpdateWBS(BaseModel):
    id: str = None
    name: str = None
    description: str = None
    project_id: str = None
    user_id: str = None
    cost_ids: Optional[List[int]]

    class Config:
        orm_mode = True


class DisplayDocument(BaseModel):
    id: str
    name: str = None
    title: str = None
    description: str = None
    # fedrisk_object_type: str = None
    # fedrisk_object_id: int = None
    # fedrisk_object_object: FedriskObjectType = None
    # created_date: datetime = None
    # last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayDocumentID(BaseModel):
    id: str
    document: DisplayDocument

    class Config:
        orm_mode = True


class DisplayWBSCost(BaseModel):
    wbs_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayWBS(BaseModel):
    id: str
    name: str
    description: str = None
    project_id: str
    user_id: str
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    costs: List[DisplayWBSCost] = []

    class Config:
        orm_mode = True


class DisplayProjectWBS(BaseModel):
    items: List[DisplayWBS] = []
    total: int

    class Config:
        orm_mode = True
        extra = "allow"
