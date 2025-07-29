from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import RiskImpact
from fedrisk_api.schema.risk_impact import CreateRiskImpact, UpdateRiskImpact


def create_risk_impact(db: Session, risk_impact: CreateRiskImpact):
    new_risk_impact = RiskImpact(**risk_impact.dict())
    db.add(new_risk_impact)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_risk_impact)
    return new_risk_impact


def get_all_risk_impacts(db: Session):
    return db.query(RiskImpact).all()


def get_risk_impact(db: Session, id: int):
    return db.query(RiskImpact).filter(RiskImpact.id == id).first()


def update_risk_impact(db: Session, id: int, risk_impact: UpdateRiskImpact):
    existing_risk_impact = db.query(RiskImpact).filter(RiskImpact.id == id)
    if not existing_risk_impact.first():
        return 0
    existing_risk_impact.update(risk_impact.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_risk_impact(db: Session, id: int):
    existing_risk_impact = db.query(RiskImpact).filter(RiskImpact.id == id)
    if not existing_risk_impact.first():
        return 0

    existing_risk_impact.delete(synchronize_session=False)
    db.commit()
    return 1
