from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import RiskLikelihood
from fedrisk_api.schema.risk_likelihood import CreateRiskLikelihood, UpdateRiskLikelihood


def create_risk_likelihood(db: Session, risk_likelihood: CreateRiskLikelihood):
    new_risk_likelihood = RiskLikelihood(**risk_likelihood.dict())
    db.add(new_risk_likelihood)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_risk_likelihood)
    return new_risk_likelihood


def get_all_risk_likelihoods(db: Session):
    return db.query(RiskLikelihood).all()


def get_risk_likelihood(db: Session, id: int):
    return db.query(RiskLikelihood).filter(RiskLikelihood.id == id).first()


def update_risk_likelihood(db: Session, id: int, risk_likelihood: UpdateRiskLikelihood):
    existing_risk_likelihood = db.query(RiskLikelihood).filter(RiskLikelihood.id == id)
    if not existing_risk_likelihood.first():
        return 0
    existing_risk_likelihood.update(risk_likelihood.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_risk_likelihood(db: Session, id: int):
    existing_risk_likelihood = db.query(RiskLikelihood).filter(RiskLikelihood.id == id)
    if not existing_risk_likelihood.first():
        return 0

    existing_risk_likelihood.delete(synchronize_session=False)
    db.commit()
    return 1
