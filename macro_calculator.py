# EXCERPT - Rαphael (proprietary project)
# Source: app/domain/nutrition.py
#
# Shared alongside budget_calculator.py to show the same architectural
# pattern applied to a completely different problem domain (nutrition
# science instead of personal finance) — both are pure, dependency-free
# calculators that sit at the core of Rαphael's hexagonal architecture.
#
# Worth noting for reviewers: the MIN_SAFE_CALORIES floor near the bottom
# is a deliberate product/engineering decision, not an oversight — the
# calculator will not recommend a calorie target below a commonly-cited
# safe minimum for unsupervised daily intake, regardless of how aggressive
# the underlying arithmetic would otherwise suggest.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MacroTargets:
    bmr: float  # Basal Metabolic Rate — calories burned at total rest
    tdee: float  # Total Daily Energy Expenditure — BMR adjusted for activity
    calorie_target: float  # TDEE adjusted for goal, floored at a safe minimum
    protein_g: float
    carbs_g: float
    fat_g: float


class MacroCalculator:
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
    }

    # -500/day is the traditional "1 lb of fat per week" deficit
    # (3500 kcal ≈ 1 lb); +300 is a conservative surplus chosen to favor
    # muscle gain over fat gain.
    GOAL_CALORIE_ADJUSTMENT = {
        "cut": -500,
        "maintain": 0,
        "bulk": 300,
    }

    # Higher protein during a cut than a maintain/bulk — extra protein in
    # a calorie deficit helps preserve muscle mass that would otherwise be
    # at greater risk of being lost.
    PROTEIN_G_PER_KG = {
        "cut": 2.2,
        "maintain": 1.8,
        "bulk": 1.8,
    }

    FAT_PERCENT_OF_CALORIES = 0.25

    # Deliberate safety floor — see module header comment above.
    MIN_SAFE_CALORIES = {"male": 1500, "female": 1200}

    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, biological_sex: str) -> float:
        """Mifflin-St Jeor equation — generally considered more accurate
        for modern populations than the older Harris-Benedict formula."""
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        return base + 5 if biological_sex == "male" else base - 161

    @classmethod
    def calculate_tdee(cls, bmr: float, activity_level: str) -> float:
        return bmr * cls.ACTIVITY_MULTIPLIERS[activity_level]

    @classmethod
    def calculate_targets(cls, user) -> MacroTargets:
        bmr = cls.calculate_bmr(user.weight_kg, user.height_cm, user.age, user.biological_sex)
        tdee = cls.calculate_tdee(bmr, user.activity_level)

        raw_calorie_target = tdee + cls.GOAL_CALORIE_ADJUSTMENT[user.goal]
        safety_floor = cls.MIN_SAFE_CALORIES[user.biological_sex]
        calorie_target = max(raw_calorie_target, safety_floor)

        protein_g = cls.PROTEIN_G_PER_KG[user.goal] * user.weight_kg
        protein_kcal = protein_g * 4

        fat_kcal = calorie_target * cls.FAT_PERCENT_OF_CALORIES
        fat_g = fat_kcal / 9

        carbs_kcal = max(calorie_target - protein_kcal - fat_kcal, 0.0)
        carbs_g = carbs_kcal / 4

        return MacroTargets(
            bmr=bmr,
            tdee=tdee,
            calorie_target=calorie_target,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
        )
