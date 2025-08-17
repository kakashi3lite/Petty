from typing import Any


def evaluate_rules(profile: dict[str, Any]) -> dict[str, Any]:
    actions = {}
    species = profile.get("species")
    life_stage = profile.get("life_stage")
    bcs = profile.get("body_condition_score")

    if species == "cat":
        actions["diet_must_be"] = "carnivorous"
    elif species == "dog":
        actions["diet_must_be"] = "omnivorous"

    if life_stage == "puppy" or life_stage == "kitten":
        actions["life_stage_nutrition"] = "growth-high-protein"
    elif life_stage == "senior":
        actions["recommend_joint_support"] = True

    if isinstance(bcs, (int, float)) and bcs >= 7:
        actions["weight_management"] = True

    return actions
