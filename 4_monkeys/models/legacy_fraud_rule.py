"""Illustrative inventory-only synthetic fraud heuristic (not a validated model)."""
def fraud_risk_score(amount_eur:float, velocity_24h:int, international:bool)->float:
    return min(.99, .02+.000001*max(amount_eur,0)+.045*max(velocity_24h-3,0)+(.12 if international else 0))
