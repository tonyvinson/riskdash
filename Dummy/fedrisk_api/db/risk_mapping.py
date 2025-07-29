from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import RiskMapping
from fedrisk_api.schema.risk_mapping import CreateRiskMapping, UpdateRiskMapping


def create_risk_mapping(db: Session, risk_mapping: CreateRiskMapping):
    new_risk_mapping = RiskMapping(**risk_mapping.dict())
    db.add(new_risk_mapping)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_risk_mapping)
    return new_risk_mapping


def get_all_risk_mappings(db: Session):
    return db.query(RiskMapping).all()


def get_risk_mapping(db: Session, id: int):
    return db.query(RiskMapping).filter(RiskMapping.id == id).first()


def update_risk_mapping(db: Session, id: int, risk_mapping: UpdateRiskMapping):
    existing_risk_mapping = db.query(RiskMapping).filter(RiskMapping.id == id)
    if not existing_risk_mapping.first():
        return 0
    existing_risk_mapping.update(risk_mapping.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_risk_mapping(db: Session, id: int):
    existing_risk_mapping = db.query(RiskMapping).filter(RiskMapping.id == id)
    if not existing_risk_mapping.first():
        return 0

    existing_risk_mapping.delete(synchronize_session=False)
    db.commit()
    return 1
