# EXCERPT - Rαphael (proprietary project)
# Source: app/domain/budget.py
#
# This is one file from Rαphael's domain layer, shared to demonstrate the
# project's architecture. Rαphael follows a hexagonal ("ports and adapters")
# structure: this file has zero imports from a database library, a web
# framework, or any external API. It only does arithmetic on plain Python
# objects, which means it can be fully unit-tested without a database, a
# server, or any network access running at all.
#
# The rest of the application (the database models, the API routes, the
# repositories that move data in and out of storage) is proprietary and
# not included here. This file is shown in isolation to illustrate the
# separation of concerns, not as a complete working module.


from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class BudgetBreakdown:
    """The result of one weekly budget calculation - everything the API
    and UI need to explain *why* the food budget is what it is, not just
    the final number."""

    weekly_income: float
    weekly_fixed_expenses: float
    weekly_savings_contribution: float
    weekly_food_budget: float


class BudgetCalculator:
    @staticmethod
    def normalize_to_weekly(amount: float, frequency: str) -> float:
        """Converts a recurring amount to its weekly equivalent.
        Monthly uses 12/52 rather than a flat /4 - a year has 52.18 weeks,
        not 48, so dividing a monthly figure by 4 would overstate it."""
        if frequency == "weekly":
            return amount
        if frequency == "monthly":
            return amount * 12 / 52
        raise ValueError(
            f"normalize_to_weekly only handles 'weekly' or 'monthly', got {frequency!r}"
        )

    @classmethod
    def _weekly_recurring_total(cls, entries) -> float:
        return sum(
            cls.normalize_to_weekly(entry.amount, entry.frequency)
            for entry in entries
            if entry.frequency != "one_time"
        )

    @staticmethod
    def _one_time_total_in_week(expenses, week_start: date) -> float:
        """One-off expenses aren't smoothed across weeks - they only count
        in the specific week they actually happened."""
        week_end = week_start + timedelta(days=6)
        return sum(
            expense.amount
            for expense in expenses
            if expense.frequency == "one_time" and week_start <= expense.expense_date <= week_end
        )

    @staticmethod
    def _weekly_savings_contribution(goal, today: date) -> float:
        """Spreads the remaining savings target evenly across the weeks
        left until the target date. No target date set yet -> no savings
        pressure applied yet, which is a deliberate default, not a bug."""
        if goal is None or goal.target_date is None:
            return 0.0
        days_remaining = (goal.target_date - today).days
        weeks_remaining = max(days_remaining / 7, 1)
        return goal.target_amount / weeks_remaining

    @classmethod
    def calculate_weekly_food_budget(
        cls,
        incomes,
        expenses,
        savings_goal,
        week_start: date,
        today: date | None = None,
    ) -> BudgetBreakdown:
        """today defaults to the real current date when not supplied.
        Tests can pass a fixed date instead, so results are fully
        reproducible rather than depending on when the test happens to run -
        a deliberate choice to keep this function free of hidden state."""
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
