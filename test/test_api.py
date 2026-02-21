# Test type: Integration
# Validation: All 5 API endpoints with real HTTP calls using challenge example data
# Command: cd backend && pytest ../test/test_api.py -v --asyncio-mode=auto

import pytest
import httpx
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app

BASE = "/blackrock/challenge/v1"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ---- 1. Transaction Parser ----

@pytest.mark.asyncio
async def test_parse_transactions(client):
    """Test /transactions:parse with challenge example expenses."""
    async with client as c:
        response = await c.post(f"{BASE}/transactions:parse", json={
            "expenses": [
                {"date": "2023-10-12 20:15:00", "amount": 250},
                {"date": "2023-02-28 15:49:00", "amount": 375},
                {"date": "2023-07-01 21:59:00", "amount": 620},
                {"date": "2023-12-17 08:09:00", "amount": 480},
            ]
        })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4

    # Verify specific calculations
    # 250 -> ceiling 300, remanent 50
    t0 = next(t for t in data if t["amount"] == 250)
    assert t0["ceiling"] == 300
    assert t0["remanent"] == 50

    # 375 -> ceiling 400, remanent 25
    t1 = next(t for t in data if t["amount"] == 375)
    assert t1["ceiling"] == 400
    assert t1["remanent"] == 25

    # 620 -> ceiling 700, remanent 80
    t2 = next(t for t in data if t["amount"] == 620)
    assert t2["ceiling"] == 700
    assert t2["remanent"] == 80

    # 480 -> ceiling 500, remanent 20
    t3 = next(t for t in data if t["amount"] == 480)
    assert t3["ceiling"] == 500
    assert t3["remanent"] == 20


@pytest.mark.asyncio
async def test_parse_exact_multiple():
    """Amount that is already a multiple of 100 should have remanent 0."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        response = await c.post(f"{BASE}/transactions:parse", json={
            "expenses": [{"date": "2023-01-01 00:00:00", "amount": 500}]
        })
    assert response.status_code == 200
    data = response.json()
    assert data[0]["ceiling"] == 500
    assert data[0]["remanent"] == 0


# ---- 2. Transaction Validator ----

@pytest.mark.asyncio
async def test_validate_transactions(client):
    """Test /transactions:validator with valid transactions."""
    async with client as c:
        response = await c.post(f"{BASE}/transactions:validator", json={
            "wage": 50000,
            "transactions": [
                {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
                {"date": "2023-02-28 15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
            ]
        })
    assert response.status_code == 200
    data = response.json()
    assert len(data["valid"]) == 2
    assert len(data["invalid"]) == 0


@pytest.mark.asyncio
async def test_validate_invalid_transactions(client):
    """Transactions with negative amounts should be invalid."""
    async with client as c:
        response = await c.post(f"{BASE}/transactions:validator", json={
            "wage": 50000,
            "transactions": [
                {"date": "2023-01-01 00:00:00", "amount": -100, "ceiling": 0, "remanent": 100},
            ]
        })
    assert response.status_code == 200
    data = response.json()
    assert len(data["invalid"]) == 1
    assert "non-negative" in data["invalid"][0]["message"].lower()


# ---- 3. Temporal Constraints Filter ----

@pytest.mark.asyncio
async def test_filter_transactions(client):
    """Test /transactions:filter with challenge example q, p, k."""
    transactions = [
        {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"date": "2023-02-28 15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
        {"date": "2023-07-01 21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
        {"date": "2023-12-17 08:09:00", "amount": 480, "ceiling": 500, "remanent": 20},
    ]
    async with client as c:
        response = await c.post(f"{BASE}/transactions:filter", json={
            "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
            "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
            "k": [
                {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
                {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
            ],
            "transactions": transactions,
        })
    assert response.status_code == 200
    data = response.json()

    # Verify k results: k1 should be 75, k2 should be 145
    k_results = data["k_results"]
    assert len(k_results) == 2
    assert k_results[0]["amount"] == 75.0  # Mar-Nov: only 250's remanent (75)
    assert k_results[1]["amount"] == 145.0  # Full year: 25 + 0 + 75 + 45


# ---- 4. Returns (NPS) ----

@pytest.mark.asyncio
async def test_returns_nps(client):
    """Test /returns:nps with challenge example data."""
    async with client as c:
        response = await c.post(f"{BASE}/returns:nps", json={
            "age": 29,
            "wage": 50000,
            "inflation": 5.5,
            "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
            "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
            "k": [
                {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
                {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
            ],
            "transactions": [
                {"date": "2023-10-12 20:15:00", "amount": 250},
                {"date": "2023-02-28 15:49:00", "amount": 375},
                {"date": "2023-07-01 21:59:00", "amount": 620},
                {"date": "2023-12-17 08:09:00", "amount": 480},
            ]
        })
    assert response.status_code == 200
    data = response.json()
    assert "savingsByDates" in data
    assert len(data["savingsByDates"]) == 2

    # Full year k-period: amount=145, NPS profit should be ~86.9
    full_year = data["savingsByDates"][1]
    assert full_year["amount"] == 145.0
    assert full_year["taxBenefit"] == 0.0  # income 600000 < 700000


# ---- 5. Returns (Index Fund) ----

@pytest.mark.asyncio
async def test_returns_index(client):
    """Test /returns:index with challenge example data."""
    async with client as c:
        response = await c.post(f"{BASE}/returns:index", json={
            "age": 29,
            "wage": 50000,
            "inflation": 5.5,
            "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
            "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
            "k": [
                {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
                {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
            ],
            "transactions": [
                {"date": "2023-10-12 20:15:00", "amount": 250},
                {"date": "2023-02-28 15:49:00", "amount": 375},
                {"date": "2023-07-01 21:59:00", "amount": 620},
                {"date": "2023-12-17 08:09:00", "amount": 480},
            ]
        })
    assert response.status_code == 200
    data = response.json()
    assert len(data["savingsByDates"]) == 2

    # Full year: amount=145, Index profit should be ~1684.5
    full_year = data["savingsByDates"][1]
    assert full_year["amount"] == 145.0
    assert full_year["taxBenefit"] == 0.0  # No tax benefit for index fund


# ---- 6. Performance Endpoint ----

@pytest.mark.asyncio
async def test_performance(client):
    """Test /performance endpoint returns expected fields."""
    async with client as c:
        response = await c.get(f"{BASE}/performance")
    assert response.status_code == 200
    data = response.json()
    assert "time" in data
    assert "memory" in data
    assert "threads" in data
    assert "MB" in data["memory"]


# ---- 7. Health Check ----

@pytest.mark.asyncio
async def test_health(client):
    """Test /health endpoint."""
    async with client as c:
        response = await c.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
