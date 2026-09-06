# EXCERPT - Rαphael (proprietary project)
# Source: app/adapters/db/repositories.py (trimmed - full file handles
# several more entities following the identical pattern)
#
# This is the piece that completes the story the other two snippets don't
# show: how domain objects (plain dataclasses, see budget_calculator.py /
# macro_calculator.py) get converted to and from actual database rows.
#
# Every function here does exactly one of two things - takes a domain
# object and saves it as a database row, or reads a database row and
# converts it back into a domain object. Domain code never imports a
# database library directly; this file is the only place that boundary
# gets crossed, which is what makes the domain layer swappable and
# database-agnostic.

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session


def _user_to_domain(row) -> "User":
    return User(
        id=row.id,
        weight_kg=row.weight_kg,
        height_cm=row.height_cm,
        age=row.age,
        biological_sex=row.biological_sex,
        activity_level=row.activity_level,
        goal=row.goal,
    )


def create_user(db: Session, user: "User") -> "User":
    row = UserORM(
        id=user.id,
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        age=user.age,
        biological_sex=user.biological_sex,
        activity_level=user.activity_level,
        goal=user.goal,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _user_to_domain(row)


def get_user(db: Session, user_id: UUID) -> "User | None":
    row = db.get(UserORM, user_id)
    return _user_to_domain(row) if row else None


def _income_to_domain(row) -> "Income":
    return Income(
        id=row.id,
        user_id=row.user_id,
        amount=row.amount,
        frequency=row.frequency,
        description=row.description,
        income_date=row.income_date,
    )


def create_income(db: Session, income: "Income") -> "Income":
    row = IncomeORM(
        id=income.id,
        user_id=income.user_id,
        amount=income.amount,
        frequency=income.frequency,
        description=income.description,
        income_date=income.income_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _income_to_domain(row)


def get_incomes_for_user(db: Session, user_id: UUID) -> list["Income"]:
    rows = db.query(IncomeORM).filter_by(user_id=user_id).all()
    return [_income_to_domain(row) for row in rows]


# NOTE: User, Income, UserORM, and IncomeORM are Rαphael's actual domain
# dataclasses and SQLAlchemy models, omitted here since they're shown in
# full in budget_calculator.py / macro_calculator.py's sibling files in
# the private repository. This excerpt focuses on the conversion pattern
# itself rather than reproducing the full model definitions.
