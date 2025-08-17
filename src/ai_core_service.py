from typing import Any

from . import knowledge_base  # noqa: F401


class AICoreService:
    def get_holistic_pet_plan(self, profile: dict[str, Any]) -> dict[str, Any]:
        # Minimal stub plan for wiring (replace with full logic)
        name = profile.get("name", "Buddy")
        return {
            "pet_profile": profile,
            "nutritional_plan": {
                "rer_calories_per_day": 700,
                "mer_calories_per_day": 1120,
                "recommended_macronutrients": {"protein_min_grams": 80},
                "suggested_foods": [{"product_name": "BrandX Senior Dog Food"}],
            },
            "health_alerts": [],
            "activity_plan": {
                "recommended_daily_exercise_minutes": 60,
                "suggested_activities": ["puzzle feeder", "long walks"],
            },
        }
