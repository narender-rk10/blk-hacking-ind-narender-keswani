"""Strategy Pattern — NPS vs Index Fund calculation strategies."""

from abc import ABC, abstractmethod
from utils.tax_calculator import calculate_tax
from core.config import settings


class InvestmentStrategy(ABC):
    """Base strategy for investment return calculation."""

    @abstractmethod
    def get_rate(self) -> float:
        ...

    @abstractmethod
    def calculate_tax_benefit(self, amount: float, annual_income: float) -> float:
        ...

    def calculate_returns(self, amount: float, t: int, inflation: float) -> dict:
        """
        Calculate inflation-adjusted compound interest returns.

        A = P * (1 + r)^t
        A_real = A / (1 + inflation/100)^t
        profit = A_real - P
        """
        rate = self.get_rate()
        A = amount * ((1 + rate) ** t)
        inflation_factor = (1 + inflation / 100) ** t
        A_real = A / inflation_factor
        profit = round(A_real - amount, 2)
        return {"amount": round(amount, 2), "profit": profit}


class NPSStrategy(InvestmentStrategy):
    """National Pension Scheme — 7.11% annual rate with tax benefits."""

    def get_rate(self) -> float:
        return settings.NPS_RATE

    def calculate_tax_benefit(self, amount: float, annual_income: float) -> float:
        """
        NPS tax benefit:
        Deduction = min(invested, 10% of annual_income, 200000)
        Benefit = Tax(income) - Tax(income - deduction)
        """
        deduction = min(
            amount,
            settings.NPS_INCOME_PERCENT * annual_income,
            settings.NPS_MAX_DEDUCTION,
        )
        tax_before = calculate_tax(annual_income)
        tax_after = calculate_tax(annual_income - deduction)
        return round(tax_before - tax_after, 2)


class IndexFundStrategy(InvestmentStrategy):
    """NIFTY 50 Index Fund — 14.49% annual rate, no tax benefits."""

    def get_rate(self) -> float:
        return settings.INDEX_RATE

    def calculate_tax_benefit(self, amount: float, annual_income: float) -> float:
        return 0.0


class ReturnsCalculator:
    """
    Factory-style calculator that uses a strategy to compute returns.

    t = max(60 - age, 5) for investment period.
    """

    def __init__(self, strategy: InvestmentStrategy):
        self.strategy = strategy

    def calculate(
        self, amount: float, age: int, annual_income: float, inflation: float
    ) -> dict:
        t = max(settings.RETIREMENT_AGE - age, settings.MIN_INVESTMENT_YEARS)
        result = self.strategy.calculate_returns(amount, t, inflation)
        result["taxBenefit"] = self.strategy.calculate_tax_benefit(
            amount, annual_income
        )
        return result

    def calculate_for_k_periods(
        self, k_results: list, age: int, annual_income: float, inflation: float
    ) -> list:
        """Calculate returns for each k period's aggregated amount."""
        savings_by_dates = []
        for k in k_results:
            amount = k["amount"]
            result = self.calculate(amount, age, annual_income, inflation)
            savings_by_dates.append(
                {
                    "start": k["start"],
                    "end": k["end"],
                    "amount": result["amount"],
                    "profit": result["profit"],
                    "taxBenefit": result["taxBenefit"],
                }
            )
        return savings_by_dates
