# from sqlalchemy.exc import IntegrityError
from fedrisk_api.db import tenant as db_tenant

# from fedrisk_api.db.database import get_db
# from fedrisk_api.schema import task as schema_tenant


def update_tenant_webhook_api_key(db, tenant_id, webhook_api_key):
    """Updates a tenant webhook_api_key."""
    # update_tenant_obj = schema_tenant.UpdateTenantWebhookApiKey(
    #     webhook_api_key=webhook_api_key,
    # )
    return db_tenant.update_tenant_webhook_api_key(
        db=db, tenant_id=tenant_id, webhook_api_key=webhook_api_key
    )
