"""Illustrative inventory-only pricing rule (not used for actual loans)."""
def annual_rate(pd_default:float, loan_term_months:int)->float:
    return .035+ .48*pd_default+.0008*max(loan_term_months-12,0)/12
