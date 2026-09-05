from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.models import Expense, Income, SavingsGoal


@dataclass
class BudgetBreakdown:
    """The result of one weekly budget calculation — everything the API
    and, later, the UI need to explain *why* the food budget is what it is,
    not just the final number."""

    weekly_income: float
    weekly_fixed_expenses: float
    weekly_savings_contribution: float
    weekly_food_budget: float


class BudgetCalculator:
    @staticmethod
    def normalize_to_weekly(amount: float, frequency: str) -> float:
        """Converts a recurring amount to its weekly equivalent.
        Monthly uses 12/52 rather than a flat /4 — a year has 52.18 weeks,
        not 48, so dividing a monthly figure by 4 would overstate it."""
        if frequency == "weekly":
            return amount
        if frequency == "monthly":
            return amount * 12 / 52
        raise ValueError(
            f"normalize_to_weekly only handles 'weekly' or 'monthly', got {frequency!r}"
        )

    @classmethod
    def _weekly_recurring_total(cls, entries: list[Income] | list[Expense]) -> float:
        return sum(
            cls.normalize_to_weekly(entry.amount, entry.frequency)
            for entry in entries
            if entry.frequency != "one_time"
        )

    @staticmethod
    def _one_time_total_in_week(expenses: list[Expense], week_start: date) -> float:
        """One-off expenses aren't smoothed across weeks — they only count
        in the specific week they actually happened."""
        week_end = week_start + timedelta(days=6)
        return sum(
            expense.amount
            for expense in expenses
            if expense.frequency == "one_time" and week_start <= expense.expense_date <= week_end
        )

    @staticmethod
    def _weekly_savings_contribution(goal: SavingsGoal | None, today: date) -> float:
        """Spreads the remaining savings target evenly across the weeks
        left until the target date. No target date set yet -> no savings
        pressure applied yet, which is a deliberate default, not a bug.

        Known simplification: if target_date has already passed, this
        floors to 1 week remaining rather than erroring — good enough for
        Phase 1, worth revisiting once overdue-goal handling matters."""
        if goal is None or goal.target_date is None:
            return 0.0
        days_remaining = (goal.target_date - today).days
        weeks_remaining = max(days_remaining / 7, 1)
        return goal.target_amount / weeks_remaining

    @classmethod
    def calculate_weekly_food_budget(
        cls,
        incomes: list[Income],
        expenses: list[Expense],
        savings_goal: SavingsGoal | None,
        week_start: date,
        today: date | None = None,
    ) -> BudgetBreakdown:
        """today defaults to the real current date when not supplied —
        callers in the API/application layer don't need to think about it.
        Tests, however, can pass a fixed date so results are reproducible
        instead of silently drifting a little differently every day."""
        today = today or date.today()

        weekly_income = cls._weekly_recurring_total(incomes)
        weekly_fixed_expenses = cls._weekly_recurring_total(
            expenses
        ) + cls._one_time_total_in_week(expenses, week_start)
        weekly_savings = cls._weekly_savings_contribution(savings_goal, today)

        food_budget = weekly_income - weekly_fixed_expenses - weekly_savings

        return BudgetBreakdown(
            weekly_income=weekly_income,
            weekly_fixed_expenses=weekly_fixed_expenses,
            weekly_savings_contribution=weekly_savings,
            weekly_food_budget=max(food_budget, 0.0),
        )
