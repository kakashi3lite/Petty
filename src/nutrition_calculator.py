def calculate_rer(weight_kg: float) -> float:
    return 70.0 * (weight_kg ** 0.75)

def calculate_mer(rer: float, activity_level: str) -> float:
    factors = {
        "weight_loss": 1.0,
        "inactive": 1.2,
        "typical": 1.6,
        "active": 2.0,
        "working": 3.0,
    }
    return rer * factors.get(activity_level, 1.6)
