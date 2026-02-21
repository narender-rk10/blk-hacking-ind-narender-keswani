"""Pydantic v2 models for request/response validation."""

from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


def normalize_date(v: str) -> str:
    """Parse any date string and return normalized format. Fast path for ISO dates."""
    try:
        dt = datetime.fromisoformat(v)
    except (ValueError, TypeError):
        from dateutil import parser as dateutil_parser
        dt = dateutil_parser.parse(v)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class Expense(BaseModel):
    date: str
    amount: float

    @field_validator("date")
    @classmethod
    def parse_date(cls, v):
        return normalize_date(v)


class Transaction(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float


class QPeriod(BaseModel):
    fixed: float
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def parse_dates(cls, v):
        return normalize_date(v)


class PPeriod(BaseModel):
    extra: float
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def parse_dates(cls, v):
        return normalize_date(v)


class KPeriod(BaseModel):
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def parse_dates(cls, v):
        return normalize_date(v)


class ParseInput(BaseModel):
    """Input for /transactions:parse"""

    expenses: List[Expense]


class ValidatorInput(BaseModel):
    """Input for /transactions:validator"""

    wage: float
    transactions: List[Transaction]


class FilterInput(BaseModel):
    """Input for /transactions:filter"""

    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod] = []
    wage: float = 0
    transactions: List[dict]


class ReturnsInput(BaseModel):
    """Input for /returns:nps and /returns:index"""

    age: int
    wage: float
    inflation: float
    q: List[QPeriod] = []
    p: List[PPeriod] = []
    k: List[KPeriod] = []
    transactions: List[dict]


class SavingsByDate(BaseModel):
    start: str
    end: str
    amount: float
    profit: float
    taxBenefit: float = 0.0


class ReturnsOutput(BaseModel):
    transactionsTotalAmount: float
    transactionsTotalCeiling: float
    savingsByDates: List[SavingsByDate]
