from contextlib import asynccontextmanager
from datetime import date
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.db import repositories as repo
from app.adapters.db.orm_models import UserORM
from app.api import schemas
from app.application.compute_macro_targets import compute_macro_targets
from app.application.compute_weekly_budget import compute_weekly_budget
from app.database import Base, engine, get_db
from app.domain.models import Expense, Income, SavingsGoal, User


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates every table defined in orm_models.py if it doesn't exist yet.
    # Fine for Phase 0 — once the schema needs to change without losing
    # existing data, this gets replaced by Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Meal Budget App", lifespan=lifespan)


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """Confirms the API can reach the database and run a real query.
    If this returns successfully, the whole Phase 0 chain — config,
    engine, session, and the users table — is working."""

    user_count = db.scalar(select(func.count()).select_from(UserORM))
    return {"status": "ok", "user_count": user_count}


def _require_user(db: Session, user_id: UUID) -> User:
    """Shared by every route that attaches data to a user_id. Raises a
    clean 404 instead of letting a bad ID surface as a raw database
    error once foreign key enforcement is on."""
    user = repo.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = User(**payload.model_dump())
    return repo.create_user(db, user)


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    return _require_user(db, user_id)


@app.post("/users/{user_id}/income", response_model=schemas.IncomeOut)
def add_income(user_id: UUID, payload: schemas.IncomeCreate, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    income = Income(user_id=user_id, **payload.model_dump())
    return repo.create_income(db, income)


@app.get("/users/{user_id}/income", response_model=list[schemas.IncomeOut])
def list_income(user_id: UUID, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    return repo.get_incomes_for_user(db, user_id)


@app.post("/users/{user_id}/expenses", response_model=schemas.ExpenseOut)
def add_expense(user_id: UUID, payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    expense = Expense(user_id=user_id, **payload.model_dump())
    return repo.create_expense(db, expense)


@app.get("/users/{user_id}/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(user_id: UUID, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    return repo.get_expenses_for_user(db, user_id)


@app.put("/users/{user_id}/savings-goal", response_model=schemas.SavingsGoalOut)
def set_savings_goal(
    user_id: UUID, payload: schemas.SavingsGoalCreate, db: Session = Depends(get_db)
):
    _require_user(db, user_id)
    goal = SavingsGoal(user_id=user_id, **payload.model_dump())
    return repo.upsert_savings_goal(db, goal)


@app.get("/users/{user_id}/savings-goal", response_model=schemas.SavingsGoalOut)
def get_savings_goal(user_id: UUID, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    goal = repo.get_savings_goal_for_user(db, user_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="No savings goal set for this user")
    return goal


@app.get("/users/{user_id}/budget/weekly", response_model=schemas.WeeklyBudgetOut)
def get_weekly_budget(user_id: UUID, week_start: date, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    breakdown = compute_weekly_budget(db, user_id, week_start)
    return schemas.WeeklyBudgetOut(week_start=week_start, **breakdown.__dict__)


@app.get("/users/{user_id}/macros", response_model=schemas.MacroTargetsOut)
def get_macro_targets(user_id: UUID, db: Session = Depends(get_db)):
    user = _require_user(db, user_id)
    targets = compute_macro_targets(user)
    return schemas.MacroTargetsOut(**targets.__dict__)
