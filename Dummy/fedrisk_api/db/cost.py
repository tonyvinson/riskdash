from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Cost,
    AssessmentCost,
    AuditTestCost,
    CapPoamCost,
    ExceptionCost,
    ProjectCost,
    ProjectEvaluationCost,
    ProjectControlCost,
    RiskCost,
    TaskCost,
    WBSCost,
    WorkflowFlowchartCost,
)
from fedrisk_api.schema.cost import CreateCost, UpdateCost


def create_cost(db: Session, cost: CreateCost, tenant_id: int):
    new_cost = Cost(**cost.dict(), tenant_id=tenant_id)
    db.add(new_cost)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_cost)
    return new_cost


def get_all_costes(db: Session, tenant_id: int):
    return db.query(Cost).filter(Cost.tenant_id == tenant_id).all()


def get_cost(db: Session, id: int):
    return db.query(Cost).filter(Cost.id == id).first()


def get_cost_by_name(db: Session, name: str):
    return db.query(Cost).filter(Cost.name == name).first()


def update_cost(db: Session, id: int, cost: UpdateCost):
    existing_cost = db.query(Cost).filter(Cost.id == id)
    if not existing_cost.first():
        return 0
    existing_cost.update(cost.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_cost(db: Session, id: int):
    existing_cost = db.query(Cost).filter(Cost.id == id)
    if not existing_cost.first():
        return 0
    # delete all assessment costs
    db.query(AssessmentCost).filter(AssessmentCost.cost_id == id).delete()
    # delete all audit test costs
    db.query(AuditTestCost).filter(AuditTestCost.cost_id == id).delete()
    # delete all cap poam costs
    db.query(CapPoamCost).filter(CapPoamCost.cost_id == id).delete()
    # delete all exception costs
    db.query(ExceptionCost).filter(ExceptionCost.cost_id == id).delete()
    # delete all Project costs
    db.query(ProjectCost).filter(ProjectCost.cost_id == id).delete()
    # delete all Project Control costs
    db.query(ProjectControlCost).filter(ProjectControlCost.cost_id == id).delete()
    # delete all Project Evaluation costs
    db.query(ProjectEvaluationCost).filter(ProjectEvaluationCost.cost_id == id).delete()
    # delete all RiskCost
    db.query(RiskCost).filter(RiskCost.cost_id == id).delete()
    # delete all TaskCost
    db.query(TaskCost).filter(TaskCost.cost_id == id).delete()
    # delete all WBSCost
    db.query(WBSCost).filter(WBSCost.cost_id == id).delete()
    # delete all WorkflowFlowchartCost
    db.query(WorkflowFlowchartCost).filter(WorkflowFlowchartCost.cost_id == id).delete()
    existing_cost.delete(synchronize_session=False)
    db.commit()
    return 1
