from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateCost(BaseModel):
    name: str
    description: str = None
    price: float = None
    currency: str = None
    quantity: int = None
    sales_tax: float = None
    rn_number: str = None
    serial_number: str = None


class UpdateCost(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    quantity: Optional[int]
    sales_tax: Optional[float]
    rn_number: Optional[str]
    serial_number: Optional[str]


class DisplayCost(BaseModel):
    id: str = None
    name: str = None
    description: str = None
    price: float = None
    currency: str = None
    quantity: int = None
    sales_tax: float = None
    rn_number: str = None
    serial_number: str = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
