# Rαphael-Showcase

This repository contains a curated, public showcase of architectural patterns
and core code samples from **Rαphael**, a proprietary fitness and finance
mobile application that helps users track wellness goals alongside their
meal budgets.

Rαphael is currently in active development (prototype). Because the full
codebase is proprietary, this repository shares a small set of
self-contained excerpts chosen to demonstrate architecture and coding
approach rather than the complete, working system.

## What Rαphael does

Rαphael combines personal budgeting with nutrition planning: it tracks
income, expenses, and savings goals to compute how much a user can spend
on food each week, then generates calorie and macronutrient targets based
on the user's body stats and fitness goal - with the eventual aim of
recommending specific, budget-accurate meal plans.

## Architecture

Rαphael follows a **hexagonal ("ports and adapters") architecture**, split
into three layers:

```
domain/         pure business logic - zero external dependencies
application/    orchestration - coordinates domain logic and data access
adapters/       swappable, external-facing - database, third-party APIs, etc.
```

The core idea: business logic (how a budget is calculated, how macro
targets are derived) is written as plain Python with no awareness of
databases, web frameworks, or external services. That logic is testable
in isolation, and the surrounding infrastructure - SQLite today, a
different database or a third-party pricing API later - can change
without touching it.

## What's included in this repository

| File | What it demonstrates |
|---|---|
| `snippets/budget_calculator.py` | Pure domain logic for turning income, expenses, and a savings goal into a weekly food budget. No database or framework imports. |
| `snippets/macro_calculator.py` | Pure domain logic applying the Mifflin-St Jeor equation to compute calorie and macro targets, including a deliberate safety floor on minimum calorie recommendations. |
| `snippets/repository_pattern.py` | A trimmed look at the adapter layer that converts between domain objects and database rows - the boundary that keeps the two previous files free of any database dependency. |

Each file includes a header comment explaining its origin and context.

## What's not included

This is a small, deliberate excerpt, not a working application. Omitted:
the full database schema and API surface, the meal-planning and grocery-
pricing logic, third-party API integrations, and the mobile client. These
remain proprietary.

## Tech stack (of the full project)

Python · FastAPI · SQLAlchemy · Pydantic · SQLite (dev) / PostgreSQL (prod)
· React Native

## Development approach

Rαphael is being built with a Waterfall-then-RAD hybrid: architectural
foundations (data model, layer boundaries) are planned upfront, then
individual features are built and tested iteratively on top of that
foundation, one working, demoable slice at a time.
