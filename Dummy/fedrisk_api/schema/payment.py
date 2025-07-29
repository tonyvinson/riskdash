from typing import Optional

from pydantic import BaseModel, EmailStr, constr


class TenantAdminUserDetail(BaseModel):
    first_name: Optional[constr(min_length=1)] = None
    last_name: Optional[constr(min_length=1)] = None
    email: EmailStr
    organization: Optional[constr(min_length=1)] = None
    tenant_id: int


class TenantAdminUpdateUserDetail(BaseModel):
    first_name: Optional[constr(min_length=1)] = None
    last_name: Optional[constr(min_length=1)] = None
    email: EmailStr
    organization: Optional[constr(min_length=1)] = None


class RetrieveUpcomingInvoice(BaseModel):
    customer_id: str


class CreateSubscriptionDetail(BaseModel):
    plan: str
    payment_method_id: str
    customer_id: str
    price_key: str
    member_count: int
    status: str
    tenant_id: str
    trial_period_days: Optional[int] = None
    is_active: bool


class CreatePaymentMethod(BaseModel):
    address_city: str
    address_country: str
    address_line_1: str
    address_line_2: str
    address_postal_code: str
    address_state: str
    customer_id: str
    type: str
    card_number: str
    card_exp_month: str
    card_exp_year: str
    card_cvc: str


class UpdatePaymentMethod(BaseModel):
    payment_method_id: str
    address_city: str
    address_country: str
    address_line_1: str
    address_line_2: str
    address_postal_code: str
    address_state: str
    customer_id: str
    type: str
    # card_number: str
    card_exp_month: str
    card_exp_year: str
    # card_cvc: str


class ListPaymentMethods(BaseModel):
    customer_id: str
    type: str


class CreatePaymentIntent(BaseModel):
    amount: int
    currency: str
    customer: str
    description: str
    payment_method: str


class DetachPaymentMethod(BaseModel):
    payment_method_id: str


class CustomerDefaultPaymentMethod(BaseModel):
    customer: str
    payment_method_id: str
