"""Tax slab calculations for Indian simplified tax regime."""


def calculate_tax(income: float) -> float:
    """
    Calculate tax based on simplified Indian tax slabs.

    Slabs:
        0 - 7,00,000:         0%
        7,00,001 - 10,00,000: 10%
        10,00,001 - 12,00,000: 15%
        12,00,001 - 15,00,000: 20%
        Above 15,00,000:       30%
    """
    if income <= 700000:
        return 0.0
    elif income <= 1000000:
        return (income - 700000) * 0.10
    elif income <= 1200000:
        return 30000 + (income - 1000000) * 0.15
    elif income <= 1500000:
        return 60000 + (income - 1200000) * 0.20
    else:
        return 120000 + (income - 1500000) * 0.30
