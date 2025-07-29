# from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

# from fedrisk_api.db.enums import SubscriptionStatus
from fedrisk_api.db.models import Tenant


def get_tenant_customer_id(tenant_id: int, db: Session):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    return tenant.customer_id


def get_tenant_subscription_id(tenant_id: int, db: Session):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if tenant.subscription:
        return tenant.subscription.subscription_id
    return None
