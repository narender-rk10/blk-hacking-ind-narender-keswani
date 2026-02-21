# Test type: Unit
# Validation: Core calculation functions in isolation
# Command: cd backend && pytest ../test/test_business_logic.py -v

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.tax_calculator import calculate_tax
from utils.interval_tree import PeriodMatcher, parse_dt
from services.returns_service import NPSStrategy, IndexFundStrategy, ReturnsCalculator
from services.transaction_service import parse_expenses


# ---- Ceiling & Remanent Calculations ----

class TestCeilingRemanent:
    def test_basic_ceiling(self):
        """250 -> ceiling 300, remanent 50."""
        class E:
            date = "2023-01-01 00:00:00"
            amount = 250
        result = parse_expenses([E()])
        assert result[0]["ceiling"] == 300
        assert result[0]["remanent"] == 50

    def test_exact_multiple(self):
        """500 -> ceiling 500, remanent 0."""
        class E:
            date = "2023-01-01 00:00:00"
            amount = 500
        result = parse_expenses([E()])
        assert result[0]["ceiling"] == 500
        assert result[0]["remanent"] == 0

    def test_one_above_multiple(self):
        """101 -> ceiling 200, remanent 99."""
        class E:
            date = "2023-01-01 00:00:00"
            amount = 101
        result = parse_expenses([E()])
        assert result[0]["ceiling"] == 200
        assert result[0]["remanent"] == 99

    def test_zero_amount(self):
        """0 -> ceiling 0, remanent 0."""
        class E:
            date = "2023-01-01 00:00:00"
            amount = 0
        result = parse_expenses([E()])
        assert result[0]["ceiling"] == 0
        assert result[0]["remanent"] == 0

    def test_large_amount(self):
        """499999 -> ceiling 500000, remanent 1."""
        class E:
            date = "2023-01-01 00:00:00"
            amount = 499999
        result = parse_expenses([E()])
        assert result[0]["ceiling"] == 500000
        assert result[0]["remanent"] == 1

    def test_all_challenge_expenses(self):
        """Verify all 4 challenge example expenses."""
        class E:
            def __init__(self, d, a):
                self.date = d
                self.amount = a

        expenses = [
            E("2023-10-12 20:15:00", 250),
            E("2023-02-28 15:49:00", 375),
            E("2023-07-01 21:59:00", 620),
            E("2023-12-17 08:09:00", 480),
        ]
        results = parse_expenses(expenses)
        expected = [
            (300, 50),
            (400, 25),
            (700, 80),
            (500, 20),
        ]
        for r, (ceil, rem) in zip(results, expected):
            assert r["ceiling"] == ceil
            assert r["remanent"] == rem


# ---- Tax Slab Calculations ----

class TestTaxCalculator:
    def test_below_7L(self):
        assert calculate_tax(600000) == 0.0

    def test_exactly_7L(self):
        assert calculate_tax(700000) == 0.0

    def test_between_7L_10L(self):
        # 800000 -> (800000 - 700000) * 0.10 = 10000
        assert calculate_tax(800000) == 10000.0

    def test_exactly_10L(self):
        # (1000000 - 700000) * 0.10 = 30000
        assert calculate_tax(1000000) == 30000.0

    def test_between_10L_12L(self):
        # 30000 + (1100000 - 1000000) * 0.15 = 30000 + 15000 = 45000
        assert calculate_tax(1100000) == 45000.0

    def test_between_12L_15L(self):
        # 60000 + (1300000 - 1200000) * 0.20 = 60000 + 20000 = 80000
        assert calculate_tax(1300000) == 80000.0

    def test_above_15L(self):
        # 120000 + (2000000 - 1500000) * 0.30 = 120000 + 150000 = 270000
        assert calculate_tax(2000000) == 270000.0

    def test_zero_income(self):
        assert calculate_tax(0) == 0.0


# ---- Period Matching ----

class TestPeriodMatcher:
    def test_single_match(self):
        periods = [
            {"start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00", "fixed": 0}
        ]
        matcher = PeriodMatcher(periods)
        dt = parse_dt("2023-07-15 12:00:00")
        matches = matcher.find_matching(dt)
        assert len(matches) == 1

    def test_no_match(self):
        periods = [
            {"start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00", "fixed": 0}
        ]
        matcher = PeriodMatcher(periods)
        dt = parse_dt("2023-08-01 00:00:00")
        matches = matcher.find_matching(dt)
        assert len(matches) == 0

    def test_boundary_match_start(self):
        """Start date should be inclusive."""
        periods = [
            {"start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00", "fixed": 10}
        ]
        matcher = PeriodMatcher(periods)
        dt = parse_dt("2023-07-01 00:00:00")
        matches = matcher.find_matching(dt)
        assert len(matches) == 1

    def test_boundary_match_end(self):
        """End date should be inclusive."""
        periods = [
            {"start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00", "fixed": 10}
        ]
        matcher = PeriodMatcher(periods)
        dt = parse_dt("2023-07-31 23:59:00")
        matches = matcher.find_matching(dt)
        assert len(matches) == 1

    def test_q_latest_start_wins(self):
        """When multiple q periods match, latest start date wins."""
        periods = [
            {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00", "fixed": 100},
            {"start": "2023-06-01 00:00:00", "end": "2023-12-31 23:59:00", "fixed": 50},
        ]
        matcher = PeriodMatcher(periods)
        dt = parse_dt("2023-07-15 12:00:00")
        best = matcher.find_latest_start_match(dt)
        assert best["fixed"] == 50  # June start is later

    def test_q_same_start_first_in_list(self):
        """Same start date: first in list wins."""
        periods = [
            {"start": "2023-06-01 00:00:00", "end": "2023-12-31 23:59:00", "fixed": 100},
            {"start": "2023-06-01 00:00:00", "end": "2023-12-31 23:59:00", "fixed": 50},
        ]
        matcher = PeriodMatcher(periods)
        dt = parse_dt("2023-07-15 12:00:00")
        best = matcher.find_latest_start_match(dt)
        assert best["fixed"] == 100  # First in original list


# ---- Investment Returns ----

class TestReturns:
    def test_nps_returns(self):
        """NPS: age 29, t=31 years, amount=145, inflation=5.5%."""
        strategy = NPSStrategy()
        calc = ReturnsCalculator(strategy)
        result = calc.calculate(145.0, 29, 600000, 5.5)
        # A = 145 * (1.0711)^31 / (1.055)^31 - 145
        assert result["amount"] == 145.0
        # Profit should be approximately 86.9 (allow tolerance)
        assert 80 < result["profit"] < 95

    def test_index_returns(self):
        """Index: age 29, t=31 years, amount=145, inflation=5.5%."""
        strategy = IndexFundStrategy()
        calc = ReturnsCalculator(strategy)
        result = calc.calculate(145.0, 29, 600000, 5.5)
        assert result["amount"] == 145.0
        # Index profit should be much higher than NPS
        assert result["profit"] > 1000

    def test_nps_tax_benefit_zero(self):
        """Income 600000 < 700000 so tax benefit should be 0."""
        strategy = NPSStrategy()
        benefit = strategy.calculate_tax_benefit(145.0, 600000)
        assert benefit == 0.0

    def test_nps_tax_benefit_positive(self):
        """Income 1000000: tax benefit should be positive."""
        strategy = NPSStrategy()
        benefit = strategy.calculate_tax_benefit(100000, 1000000)
        # Deduction = min(100000, 100000, 200000) = 100000
        # Tax(1000000) - Tax(900000) = 30000 - 20000 = 10000
        assert benefit == 10000.0

    def test_index_no_tax_benefit(self):
        """Index fund has no tax benefit."""
        strategy = IndexFundStrategy()
        benefit = strategy.calculate_tax_benefit(100000, 1000000)
        assert benefit == 0.0

    def test_min_investment_period(self):
        """Age 58: t = max(60-58, 5) = 5 years."""
        strategy = NPSStrategy()
        calc = ReturnsCalculator(strategy)
        result = calc.calculate(1000, 58, 600000, 5.5)
        assert result["amount"] == 1000.0

    def test_above_60(self):
        """Age 65: t = max(60-65, 5) = 5 years minimum."""
        strategy = NPSStrategy()
        calc = ReturnsCalculator(strategy)
        result = calc.calculate(1000, 65, 600000, 5.5)
        # Should use t=5
        A = 1000 * (1.0711 ** 5) / (1.055 ** 5)
        expected_profit = round(A - 1000, 2)
        assert abs(result["profit"] - expected_profit) < 0.1


# ---- Compound Interest Formula Verification ----

class TestCompoundInterest:
    def test_nps_formula(self):
        """Verify: A = 145 * (1.0711)^31 = ~1219.45."""
        A = 145 * (1.0711 ** 31)
        assert 1210 < A < 1230

    def test_index_formula(self):
        """Verify: A = 145 * (1.1449)^31 = ~9619.7."""
        A = 145 * (1.1449 ** 31)
        assert 9500 < A < 9800

    def test_inflation_adjustment(self):
        """Verify: A_real = A / (1.055)^31."""
        inflation_factor = (1.055) ** 31
        assert 5.2 < inflation_factor < 5.3
