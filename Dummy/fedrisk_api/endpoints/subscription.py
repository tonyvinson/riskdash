import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import fedrisk_api.db.subscription as db_subscription
import fedrisk_api.db.tenant as db_tenant
from config.config import Settings
from fedrisk_api.db.database import get_db

# from fedrisk_api.db.enums import SubscriptionStatus
from fedrisk_api.db.models import User, Tenant
from fedrisk_api.schema.payment import (
    CreateSubscriptionDetail,
    RetrieveUpcomingInvoice,
    TenantAdminUserDetail,
    CreatePaymentMethod,
    CreatePaymentIntent,
    ListPaymentMethods,
    UpdatePaymentMethod,
    DetachPaymentMethod,
    CustomerDefaultPaymentMethod,
)
from fedrisk_api.schema.subscription import (
    CreateSubscription,
    RetrieveUpcomingInvoiceDetail,
    ListSubscriptions,
    CancelSubscription,
    ResumeSubscription,
    AvailableLicenses,
)
from fedrisk_api.service.email_service import EmailService
from fedrisk_api.service.payment_service import PaymentService
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.email_util import (
    send_payment_failure_email,
    send_payment_success_email,
    send_subscription_cancel_email,
    send_subscription_success_email,
    send_subscription_update_email,
)
from fedrisk_api.utils.permissions import (
    create_subscription_permission,
    delete_subscription_permission,
    update_subscription_permission,
    view_subscription_permission,
)
from fedrisk_api.utils.utils import (
    convert_unix_time_to_postgres_timestamp,
    # get_subscription_data,
    get_subscription_email_data,
    get_tenant_customer_data,
    # get_transaction_data,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
LOGGER = logging.getLogger(__name__)


@router.get("/get_all_plans")
def get_all_plans():
    payment_client = PaymentService(config=Settings())
    products = payment_client.get_all_products()
    return products


@router.post("/create_customer")
def create_customer(db: Session = Depends(get_db), user=Depends(custom_auth)):
    payment_client = PaymentService(config=Settings())
    customer_data = get_tenant_customer_data(user["tenant_id"], user["user_id"], db)
    customer = TenantAdminUserDetail(**customer_data)
    created_customer = payment_client.create_customer(customer)
    db_tenant.update_tenant_customer(created_customer["id"], user["tenant_id"], db)
    return {"customer_id": created_customer["id"]}


@router.post(
    "/create_payment_method",
)
def create_payment_method(
    request: CreatePaymentMethod,
):
    payment_client = PaymentService(config=Settings())
    data = {
        "address_city": request.address_city,
        "address_country": request.address_country,
        "address_line_1": request.address_line_1,
        "address_line_2": request.address_line_2,
        "address_postal_code": request.address_postal_code,
        "address_state": request.address_state,
        "customer_id": request.customer_id,
        "type": request.type,
        "card_number": request.card_number,
        "card_exp_month": request.card_exp_month,
        "card_exp_year": request.card_exp_year,
        "card_cvc": request.card_cvc,
    }
    payment_model = CreatePaymentMethod(**data)
    return payment_client.create_payment_method(payment_model)


@router.post(
    "/update_payment_method",
    dependencies=[Depends(update_subscription_permission)],
)
def update_payment_method(
    request: UpdatePaymentMethod,
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    data = {
        "payment_method_id": request.payment_method_id,
        "address_city": request.address_city,
        "address_country": request.address_country,
        "address_line_1": request.address_line_1,
        "address_line_2": request.address_line_2,
        "address_postal_code": request.address_postal_code,
        "address_state": request.address_state,
        "customer_id": request.customer_id,
        "type": request.type,
        # "card_number": request.card_number,
        "card_exp_month": request.card_exp_month,
        "card_exp_year": request.card_exp_year,
        # "card_cvc": request.card_cvc,
    }
    payment_model = UpdatePaymentMethod(**data)
    return payment_client.update_payment_method(payment_model)


@router.post("/attach_default_payment_method")
def attach_default_payment_method(
    request: CustomerDefaultPaymentMethod,
):
    payment_client = PaymentService(config=Settings())
    data = {
        "customer": request.customer,
        "payment_method_id": request.payment_method_id,
    }
    payment_model = CustomerDefaultPaymentMethod(**data)
    return payment_client.attach_default_payment_method(payment_model)


@router.post(
    "/list_payment_methods",
    dependencies=[Depends(view_subscription_permission)],
)
def list_payment_methods(
    request: ListPaymentMethods,
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    data = {
        "customer_id": request.customer_id,
        "type": request.type,
    }
    payment_model = ListPaymentMethods(**data)
    return payment_client.list_payment_methods(payment_model)


@router.get(
    "/list_customer_default_payment_method",
    dependencies=[Depends(view_subscription_permission)],
)
def list_customer_default_payment_method(db: Session = Depends(get_db), user=Depends(custom_auth)):
    payment_client = PaymentService(config=Settings())

    customer_id = db_subscription.get_tenant_customer_id(tenant_id=user["tenant_id"], db=db)

    data = {
        "customer_id": customer_id,
    }
    invoice_model = RetrieveUpcomingInvoice(**data)
    return payment_client.list_customer_default_payment_method(invoice_model)


@router.post(
    "/detach_payment_method",
    dependencies=[Depends(update_subscription_permission)],
)
def detach_payment_method(
    request: DetachPaymentMethod,
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    data = {
        "payment_method_id": request.payment_method_id,
    }
    payment_model = DetachPaymentMethod(**data)
    return payment_client.detach_payment_method(payment_model)


@router.post(
    "/list",
    dependencies=[Depends(view_subscription_permission)],
)
def list_subscriptions(
    request: ListSubscriptions,
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    data = {
        "customer": request.customer,
        "status": request.status,
    }
    payment_model = ListSubscriptions(**data)
    return payment_client.list_subscriptions(payment_model)


@router.post(
    "/create_payment_intent",
    dependencies=[Depends(create_subscription_permission)],
)
def create_payment_intent(
    request: CreatePaymentIntent,
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    data = {
        "amount": request.amount,
        "currency": request.currency,
        "customer": request.customer,
        "description": request.description,
        "payment_method": request.payment_method,
    }
    payment_model = CreatePaymentIntent(**data)
    payment_client.create_payment_intent(payment_model)
    return {"details": "payment intent created for tenant"}


@router.post(
    "/get_all_invoices",
    dependencies=[Depends(view_subscription_permission)],
)
def get_all_invoices(db: Session = Depends(get_db), user=Depends(custom_auth)):
    payment_client = PaymentService(config=Settings())

    customer_id = db_subscription.get_tenant_customer_id(tenant_id=user["tenant_id"], db=db)

    data = {
        "customer_id": customer_id,
    }
    invoice_model = RetrieveUpcomingInvoice(**data)
    return payment_client.get_all_invoices(invoice_model)


@router.post(
    "/retrieve_upcoming_invoice",
    dependencies=[Depends(view_subscription_permission)],
)
def retrieve_upcoming_invoice(
    request: RetrieveUpcomingInvoiceDetail, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    payment_client = PaymentService(config=Settings())

    # customer_id = db_subscription.get_tenant_customer_id(tenant_id=user["tenant_id"], db=db)

    data = {
        "customer_id": request.customer_id,
    }
    invoice_model = RetrieveUpcomingInvoice(**data)
    return payment_client.retrieve_upcoming_invoice(invoice_model)


@router.get(
    "/retrieve_next_payment_invoice",
    dependencies=[Depends(view_subscription_permission)],
)
def retrieve_next_payment_invoice(db: Session = Depends(get_db), user=Depends(custom_auth)):
    payment_client = PaymentService(config=Settings())
    tenant = db_tenant.get_tenant_by_id(tenant_id=user["tenant_id"], db=db)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Profile does not exists"
        )

    if not tenant.subscription or tenant.subscription.frequency.lower() == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant does not have any subscription"
        )
    customer_id = tenant.customer_id
    subscription_id = tenant.subscription.subscription_id

    try:
        return payment_client.retrieve_next_payment_invoice(customer_id, subscription_id)
    except Exception as e:
        error = str(e)
        if "cannot preview the upcoming invoice for a canceled subscription." in error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Canceled subscription does not have any upcoming invoice",
            )


@router.post(
    "/create",
    # dependencies=[Depends(create_subscription_permission)],
)
def create_subscription(
    request: CreateSubscription,
    db: Session = Depends(get_db),
    # user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())

    customer_id = db_subscription.get_tenant_customer_id(tenant_id=request.tenant_id, db=db)

    if not customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="profile not exists")
    try:
        data = {
            "tenant_id": request.tenant_id,
            "payment_method_id": request.payment_method_id,
            "customer_id": customer_id,
            "member_count": request.member_count,
            "price_key": request.price_key,
            "plan": request.plan.value,
            "status": request.status,
            "trial_period_days": request.trial_period_days,
            "is_active": 1,
        }
        # update user_license field in tenant
        if request.trial_period_days != "":
            db_tenant.update_tenant_user_licenses(request.member_count, request.tenant_id, db)
        if request.trial_period_days == "":
            db_tenant.update_tenant_user_licenses(1, request.tenant_id, db)

        subscription_data = CreateSubscriptionDetail(**data)
        return payment_client.create_subscription(subscription_data)
    except Exception as e:
        LOGGER.exception(f"Uncovered exception while creating subscription: {request.dict()}")
        error = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


@router.delete("/cancel", dependencies=[Depends(delete_subscription_permission)])
def cancel_subscription(
    request: CancelSubscription,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    # update user_license field in tenant
    db_tenant.update_tenant_user_licenses(0, user["tenant_id"], db)
    return payment_client.cancel_subscription(request.subscription_id)


@router.post(
    "/resume_subscription",
    dependencies=[Depends(update_subscription_permission)],
)
def resume_subscription(
    request: ResumeSubscription,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())
    data = {
        "subscription_id": request.subscription_id,
        # "billing_cycle_anchor": request.billing_cycle_anchor,
    }
    payment_model = ResumeSubscription(**data)
    return payment_client.resume_subscription(payment_model)


@router.post(
    "/pause_subscription",
    dependencies=[Depends(update_subscription_permission)],
)
def pause_subscription(
    request: CancelSubscription,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # get all users for tenant

    # deactivate all users on tenant
    payment_client = PaymentService(config=Settings())

    return payment_client.pause_subscription(request.subscription_id)


@router.post(
    "/unpause_subscription",
    dependencies=[Depends(update_subscription_permission)],
)
def unpause_subscription(
    request: CancelSubscription,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    payment_client = PaymentService(config=Settings())

    return payment_client.unpause_subscription(request.subscription_id)


@router.post("/stripe-webhook")
async def webhook_received(
    request: Request,
    db: Session = Depends(get_db),
):
    sig_header = request.headers.get("stripe-signature")

    payment_client = PaymentService(config=Settings())
    try:
        event = payment_client.construct_event(
            request_data=await request.body(), signature=sig_header
        )
        event_type = event["type"]
        data = event["data"]
    except Exception:
        # Invalid payload or Exception.
        LOGGER.exception("Error while verifying event")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    settings = Settings()
    email_service = EmailService(config=Settings())

    if event_type == "invoice.paid":
        customer = payment_client.get_customer_by_id(data["object"]["customer"])
        subscription = payment_client.get_subscription_by_id(data["object"]["subscription"])
        tenant_id = subscription["metadata"]["tenant_id"]
        tenant = db_tenant.get_tenant_by_id(tenant_id=tenant_id, db=db)
        price_id = subscription["items"]["data"][0]["price"]["id"]
        total_member = subscription["items"]["data"][0]["quantity"]
        free_member_count = payment_client.get_product_default_member_count(price_id)
        additional_member_count = total_member - free_member_count

        if tenant:
            subscription_data = get_subscription_data(
                subscription,
                customer,
                free_member_count,
                additional_member_count,
                True,
                tenant_id,
                SubscriptionStatus.active.value,
            )
            admin_users = (
                db.query(User)
                .filter(User.tenant_id == tenant_id, User.is_tenant_admin is True)
                .all()
            )

            transaction_data = get_transaction_data(customer, data, "Paid", tenant_id)

            db_subscription.create_transaction(**transaction_data, db=db)

            if not tenant.subscription:
                subscription_data.update(
                    {"created_at": convert_unix_time_to_postgres_timestamp(subscription["created"])}
                )
                subscription_obj = db_subscription.create_subscription(**subscription_data, db=db)

                if not subscription_obj:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription not Created"
                    )

                for admin in admin_users:
                    subscription_email_data = get_subscription_email_data(
                        subscription_data, admin.email
                    )
                    await send_subscription_success_email(
                        # email_service=email_service,
                        subscription_data=subscription_email_data
                    )
            else:
                subscription_obj = db_subscription.update_subscription(**subscription_data, db=db)

            for admin in admin_users:
                await send_payment_success_email(
                    # email_service=email_service,
                    payment_success_data={"email": admin.email},
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not exists"
            )

    elif event_type == "customer.subscription.updated":
        customer = payment_client.get_customer_by_id(data["object"]["customer"])
        subscription = payment_client.get_subscription_by_id(data["object"]["id"])
        tenant_id = subscription["metadata"]["tenant_id"]
        tenant = db_tenant.get_tenant_by_id(tenant_id=tenant_id, db=db)
        price_id = subscription["items"]["data"][0]["price"]["id"]
        total_member = subscription["items"]["data"][0]["quantity"]
        free_member_count = payment_client.get_product_default_member_count(price_id)
        additional_member_count = total_member - free_member_count

        subscription_is_active = False if subscription["cancel_at_period_end"] else True
        subscription_status = (
            SubscriptionStatus.active.value
            if subscription_is_active
            else SubscriptionStatus.canceled.value
        )
        if tenant.subscription and tenant.subscription.subscription_id:
            subscription_data = get_subscription_data(
                subscription,
                customer,
                free_member_count,
                additional_member_count,
                subscription_is_active,
                tenant_id,
                subscription_status,
            )
            subscription_obj = db_subscription.update_subscription(**subscription_data, db=db)
            admin_users = (
                db.query(User)
                .filter(User.tenant_id == tenant_id, User.is_tenant_admin is True)
                .all()
            )
            for admin in admin_users:
                await send_subscription_update_email(
                    # email_service=email_service,
                    subscription_data={"subscription": subscription["id"], "email": admin.email},
                )

    elif event_type == "invoice.payment_failed":
        subscription = payment_client.get_subscription_by_id(data["object"]["subscription"])
        tenant_id = subscription["metadata"]["tenant_id"]
        customer = payment_client.get_customer_by_id(data["object"]["customer"])
        tenant = db_tenant.get_tenant_by_id(tenant_id=tenant_id, db=db)

        if tenant:
            transaction_data = get_transaction_data(customer, data, "Failed", tenant_id)
            db_subscription.create_transaction(**transaction_data, db=db)

            admin_users = (
                db.query(User)
                .filter(User.tenant_id == tenant_id, User.is_tenant_admin is True)
                .all()
            )

            cc_retry_count = db_subscription.get_cc_retry_count(
                subscription_id=subscription["id"], db=db
            )
            if (cc_retry_count is None) or (cc_retry_count >= int(settings.CC_RETRY_COUNT)):
                payment_client.delete_subscription(subscription_id=subscription["id"])
            else:
                db_subscription.update_subscription_to_pending(
                    subscription_id=subscription["id"], db=db
                )
                db_subscription.increment_cc_retry_count_by_one(
                    subscription_id=subscription["id"], db=db
                )

            for admin in admin_users:
                await send_payment_failure_email(
                    email_service=email_service,
                    payment_fail_data={"email": admin.email},
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant or subscription not found"
            )

    elif event_type == "customer.subscription.deleted":
        subscription = payment_client.get_subscription_by_id(data["object"]["id"])
        tenant_id = subscription["metadata"]["tenant_id"]
        customer = payment_client.get_customer_by_id(data["object"]["customer"])
        tenant = db_tenant.get_tenant_by_id(tenant_id=tenant_id, db=db)
        if tenant.subscription:
            subscription_obj = db_subscription.cancel_subscription(
                tenant.subscription.subscription_id, db
            )
            admin_users = (
                db.query(User)
                .filter(User.tenant_id == tenant_id, User.is_tenant_admin is True)
                .all()
            )
            for admin in admin_users:
                await send_subscription_cancel_email(
                    # email_service=email_service,
                    subscription_fail_data={
                        "subscription": subscription["id"],
                        "email": admin.email,
                    },
                )
        # else:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant or subscription not found"
        #     )
        #     pass

    return {"status": "success"}


@router.post(
    "/available_user_licenses",
    dependencies=[Depends(update_subscription_permission)],
)
def available_user_licenses(
    request: AvailableLicenses,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):

    licenses_active = (
        db.query(User)
        .filter(User.tenant_id == user["tenant_id"])
        .filter(User.is_active == True)
        .count()
    )

    tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()

    licenses_purchased = tenant.user_licence

    licenses_requested = int(request.number_of_licenses)

    total_licenses_needed = licenses_active + licenses_requested

    LOGGER.info(f"licenses requested {licenses_requested}")
    LOGGER.info(f"licences active {licenses_active}")
    LOGGER.info(f"total_licenses_needed {total_licenses_needed}")

    if total_licenses_needed <= licenses_purchased:
        return {"status": "Yes you have sufficient licenses available"}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough licences left"
        )
