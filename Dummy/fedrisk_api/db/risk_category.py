from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import RiskCategory
from fedrisk_api.schema.risk_category import CreateRiskCategory, UpdateRiskCategory


def create_risk_category(db: Session, risk_category: CreateRiskCategory, tenant_id: int):
    new_risk_category = RiskCategory(**risk_category.dict(), tenant_id=tenant_id)
    db.add(new_risk_category)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_risk_category)
    return new_risk_category


def get_all_risk_categories(db: Session, tenant_id: int):
    return db.query(RiskCategory).filter(RiskCategory.tenant_id == tenant_id).all()


def get_risk_category(db: Session, id: int):
    return db.query(RiskCategory).filter(RiskCategory.id == id).first()


def update_risk_category(db: Session, id: int, risk_category: UpdateRiskCategory):
    existing_risk_category = db.query(RiskCategory).filter(RiskCategory.id == id)
    if not existing_risk_category.first():
        return 0
    existing_risk_category.update(risk_category.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_risk_category(db: Session, id: int):
    existing_risk_category = db.query(RiskCategory).filter(RiskCategory.id == id)
    if not existing_risk_category.first():
        return 0

    existing_risk_category.delete(synchronize_session=False)
    db.commit()
    return 1
