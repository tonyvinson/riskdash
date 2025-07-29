import enum

from pydantic import BaseModel


class Plan(enum.Enum):
    month = "month"
    year = "year"


class RetrieveUpcomingInvoiceDetail(BaseModel):
    # plan: Plan
    # price_key: str
    # member_count: int
    # state: str = None
    customer_id: str


class CreateSubscription(BaseModel):
    plan: Plan
    payment_method_id: str
    price_key: str
    member_count: int
    status: str
    tenant_id: str
    trial_period_days: int = None
    is_active: bool


class ListSubscriptions(BaseModel):
    customer: str
    status: str


class CancelSubscription(BaseModel):
    subscription_id: str


class ResumeSubscription(BaseModel):
    subscription_id: str
    # billing_cycle_anchor: str


class AvailableLicenses(BaseModel):
    number_of_licenses: int
