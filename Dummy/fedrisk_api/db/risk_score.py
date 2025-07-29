from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import RiskScore
from fedrisk_api.schema.risk_score import CreateRiskScore, UpdateRiskScore


def create_risk_score(db: Session, risk_score: CreateRiskScore):
    new_risk_score = RiskScore(**risk_score.dict())
    db.add(new_risk_score)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_risk_score)
    return new_risk_score


def get_all_risk_scores(db: Session):
    return db.query(RiskScore).all()


def get_risk_score(db: Session, id: int):
    return db.query(RiskScore).filter(RiskScore.id == id).first()


def update_risk_score(db: Session, id: int, risk_score: UpdateRiskScore):
    existing_risk_score = db.query(RiskScore).filter(RiskScore.id == id)
    if not existing_risk_score.first():
        return 0
    existing_risk_score.update(risk_score.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_risk_score(db: Session, id: int):
    existing_risk_score = db.query(RiskScore).filter(RiskScore.id == id)
    if not existing_risk_score.first():
        return 0

    existing_risk_score.delete(synchronize_session=False)
    db.commit()
    return 1
