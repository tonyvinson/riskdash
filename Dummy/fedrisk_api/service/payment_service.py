from datetime import datetime, timedelta, timezone
from importlib import import_module

from fedrisk_api.schema.payment import (
    CreateSubscriptionDetail,
    RetrieveUpcomingInvoice,
    TenantAdminUpdateUserDetail,
    TenantAdminUserDetail,
    CreatePaymentMethod,
    CreatePaymentIntent,
    ListPaymentMethods,
    UpdatePaymentMethod,
    DetachPaymentMethod,
    CustomerDefaultPaymentMethod,
)

from fedrisk_api.schema.subscription import (
    ListSubscriptions,
    ResumeSubscription,
)


class PaymentService:
    def __init__(self, config) -> None:
        self.stripe = import_module("stripe")
        self.stripe.api_key = config.STRIPE_SECRET_KEY

    def create_customer(self, profile: TenantAdminUserDetail):
        full_name = f"{profile.first_name} {profile.last_name}"
        return self.stripe.Customer.create(
            name=full_name, email=profile.email, metadata=profile.dict()
        )

    def update_customer(self, customer_id: str, updated_profile: TenantAdminUpdateUserDetail):
        updated_profile = updated_profile.dict(exclude_none=True)
        return self.stripe.Customer.modify(customer_id, **updated_profile)

    def get_customer_by_id(self, customer_id: str):
        return self.stripe.Customer.retrieve(customer_id)

    def create_payment_method(self, model: CreatePaymentMethod):
        card = {
            "number": model.card_number,
            "exp_month": model.card_exp_month,
            "exp_year": model.card_exp_year,
            "cvc": model.card_cvc,
        }

        result = self.stripe.PaymentMethod.create(
            type=model.type,
            billing_details={
                "address": {
                    "city": model.address_city,
                    "country": model.address_country,
                    "line1": model.address_line_1,
                    "line2": model.address_line_2,
                    "postal_code": model.address_postal_code,
                    "state": model.address_state,
                }
            },
            card=card,
        )
        return self.stripe.PaymentMethod.attach(
            result.id,
            customer=model.customer_id,
        )

    def update_payment_method(self, model: UpdatePaymentMethod):
        card = {
            # "number": model.card_number,
            "exp_month": model.card_exp_month,
            "exp_year": model.card_exp_year,
            # "cvc": model.card_cvc,
        }

        return self.stripe.PaymentMethod.modify(
            model.payment_method_id,
            billing_details={
                "address": {
                    "city": model.address_city,
                    "country": model.address_country,
                    "line1": model.address_line_1,
                    "line2": model.address_line_2,
                    "postal_code": model.address_postal_code,
                    "state": model.address_state,
                }
            },
            card=card,
        )

    def attach_default_payment_method(self, model: CustomerDefaultPaymentMethod):
        return self.stripe.Customer.modify(
            model.customer,
            invoice_settings={
                "default_payment_method": model.payment_method_id,
            },
        )

    def list_payment_methods(self, model: ListPaymentMethods):
        return self.stripe.Customer.list_payment_methods(
            model.customer_id,
            type=model.type,
        )

    def detach_payment_method(self, model: DetachPaymentMethod):
        return self.stripe.PaymentMethod.detach(
            model.payment_method_id,
        )

    def create_payment_intent(self, model: CreatePaymentIntent):
        return self.stripe.PaymentIntent.create(
            amount=model.amount,
            currency=model.currency,
            customer=model.customer,
            description=model.description,
            payment_method=model.payment_method,
        )

    def get_product_by_id(self, product_id):
        return self.stripe.Product.retrieve(product_id)

    def retrieve_upcoming_invoice(self, model: RetrieveUpcomingInvoice):
        # Retrieve the Invoice
        invoice = self.stripe.Invoice.upcoming(
            customer=model.customer_id,
        )

        return invoice

    def get_all_invoices(self, model: RetrieveUpcomingInvoice):
        # Retrieve the Invoice
        invoice = self.stripe.Invoice.list(
            customer=model.customer_id,
        )

        return invoice

    def get_customer_payment_method(self, customer_id):
        customer = self.get_customer_by_id(customer_id)
        try:
            dpm = customer["invoice_settings"]["default_payment_method"]
            if not dpm:
                return {}

            pm = self.stripe.PaymentMethod.retrieve(
                customer["invoice_settings"]["default_payment_method"]
            )
            return pm or {}
        except KeyError:
            return {}

    def create_subscription(self, model: CreateSubscriptionDetail):
        items = [
            {
                "price": model.price_key,
                "quantity": model.member_count,
            },
        ]
        self.stripe.Customer.modify(
            model.customer_id, invoice_settings={"default_payment_method": model.payment_method_id}
        )
        return self.stripe.Subscription.create(
            customer=model.customer_id,
            items=items,
            trial_period_days=model.trial_period_days,
            expand=["latest_invoice.payment_intent"],
            metadata={"tenant_id": model.tenant_id},
        )

    def get_subscription_by_id(self, subscription_id: str):
        return self.stripe.Subscription.retrieve(subscription_id)

    def construct_event(self, request_data: dict, signature: str):
        return self.stripe.Webhook.construct_event(
            payload=request_data, sig_header=signature, secret=self.web_hook_secrete
        )

    def list_subscriptions(self, model: ListSubscriptions):
        return self.stripe.Subscription.list(
            customer=model.customer,
            status=model.status,
        )

    def list_customer_default_payment_method(self, model: RetrieveUpcomingInvoice):
        return self.stripe.Customer.list_sources(
            model.customer_id,
            object="card",
            limit=3,
        )

    def resume_subscription(self, model: ResumeSubscription):
        return self.stripe.Subscription.delete(model.subscription_id)

    def cancel_subscription(self, subscription_id: str):
        return self.stripe.Subscription.delete(subscription_id)

    def get_all_invoice(self, subscription_id: str):
        return self.stripe.Invoice.list(subscription=subscription_id, limit=100)

    def retrieve_next_payment_invoice(self, customer_id, subscription_id):
        return self.stripe.Invoice.upcoming(customer=customer_id, subscription=subscription_id)

    def pause_subscription(self, subscription_id: str):
        current_datetime = datetime.now(timezone.utc)
        end_datetime = current_datetime + timedelta(days=365)
        return self.stripe.Subscription.modify(
            subscription_id,
            pause_collection={"behavior": "void", "resumes_at": end_datetime},
        )

    def unpause_subscription(self, subscription_id: str):
        return self.stripe.Subscription.modify(
            subscription_id,
            pause_collection="",
        )

    def get_all_products(self):
        product_data = []
        plans = self.stripe.Plan.list(active=True)

        for index, plan in enumerate(plans, 1):
            product_name = "Fedrisk " + plan["interval"] + "ly Plan"
            if plan["amount_decimal"]:
                current_product = {
                    "price_id": plan["id"],
                    "price": plan["amount_decimal"],
                    "interval": plan["interval"],
                }
                product_data.append({product_name: current_product})
        return product_data

    def delete_subscription(self, subscription_id):
        return self.stripe.Subscription.delete(subscription_id)
