from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import RiskStatus
from fedrisk_api.schema.risk_status import CreateRiskStatus, UpdateRiskStatus


def create_risk_status(db: Session, risk_status: CreateRiskStatus):
    new_risk_status = RiskStatus(**risk_status.dict())
    db.add(new_risk_status)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_risk_status)
    return new_risk_status


def get_all_risk_statuses(db: Session):
    return db.query(RiskStatus).all()


def get_risk_status(db: Session, id: int):
    return db.query(RiskStatus).filter(RiskStatus.id == id).first()


def update_risk_status(db: Session, id: int, risk_status: UpdateRiskStatus):
    existing_risk_status = db.query(RiskStatus).filter(RiskStatus.id == id)
    if not existing_risk_status.first():
        return 0
    existing_risk_status.update(risk_status.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_risk_status(db: Session, id: int):
    existing_risk_status = db.query(RiskStatus).filter(RiskStatus.id == id)
    if not existing_risk_status.first():
        return 0

    existing_risk_status.delete(synchronize_session=False)
    db.commit()
    return 1
