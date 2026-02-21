# BlackRock Hackathon — Self-Saving for Retirement

Production-grade automated retirement savings system through expense-based micro-investments.

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────┐
│  React Frontend │────>│  Nginx (port 3000)                   │
│  - Vite + React │     │  - Static files + API proxy          │
│  - Tailwind CSS │     └──────────────┬───────────────────────┘
│  - Recharts     │                    │ /blackrock/*
│  - react-window │                    ▼
│  - Zustand      │     ┌──────────────────────────────────────┐
│  - Web Workers  │     │  FastAPI Backend (port 5477)         │
└─────────────────┘     │  ┌────────────────────────────────┐  │
                        │  │  Routers                        │  │
                        │  │  /transactions:parse            │  │
                        │  │  /transactions:validator        │  │
                        │  │  /transactions:filter           │  │
                        │  │  /returns:nps                   │  │
                        │  │  /returns:index                 │  │
                        │  │  /performance                   │  │
                        │  └──────────┬─────────────────────┘  │
                        │             │                         │
                        │  ┌──────────▼─────────────────────┐  │
                        │  │  Services Layer                 │  │
                        │  │  - TransactionPipeline          │  │
                        │  │  - FilterService (bisect)       │  │
                        │  │  - ReturnsCalculator            │  │
                        │  │  - ValidatorService             │  │
                        │  └──────────┬─────────────────────┘  │
                        │             │                         │
                        │  ┌──────────▼─────────────────────┐  │
                        │  │  Utils                          │  │
                        │  │  - PeriodMatcher (O(log n))     │  │
                        │  │  - TaxCalculator                │  │
                        │  └────────────────────────────────┘  │
                        └──────────────────────────────────────┘
```

## Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Singleton** | `PerformanceMonitor` | Thread-safe metrics collection |
| **Strategy** | `NPSStrategy`, `IndexFundStrategy` | Pluggable investment calculation |
| **Pipeline** | `TransactionPipeline` | Composable processing steps |
| **Repository** | Service layer separation | Data access isolation |
| **Observer** | Middleware + Monitor | Request metrics tracking |

## Performance Optimizations

### Backend
- **Bisect interval search** — O(log n) period matching vs O(n) brute force
- **uvicorn with 4 workers** — Multi-core utilization
- **Pydantic v2** — 5-50x faster validation vs v1

### Frontend
- **react-window** — Virtual scrolling for 10^6 rows
- **React.lazy + Suspense** — Code splitting per section
- **Web Workers** — Large JSON parsing off the main thread
- **Zustand** — Minimal re-renders, no context propagation
- **Debounced inputs** — Prevent parse storms
- **Memoized components** — useMemo/useCallback throughout

## Prerequisites

- Docker 24+
- Docker Compose v2

## Quick Start

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API Docs: http://localhost:5477/docs
- ReDoc: http://localhost:5477/redoc

## Run Tests

```bash
cd backend
pip install -r requirements.txt
pytest ../test/ -v --asyncio-mode=auto
```

## API Endpoints

### 1. Transaction Parser
```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:parse \
  -H "Content-Type: application/json" \
  -d '{
    "expenses": [
      {"date": "2023-10-12 20:15:00", "amount": 250},
      {"date": "2023-02-28 15:49:00", "amount": 375},
      {"date": "2023-07-01 21:59:00", "amount": 620},
      {"date": "2023-12-17 08:09:00", "amount": 480}
    ]
  }'
```

### 2. Transaction Validator
```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:validator \
  -H "Content-Type: application/json" \
  -d '{
    "wage": 50000,
    "transactions": [
      {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50}
    ]
  }'
```

### 3. Temporal Filter
```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:filter \
  -H "Content-Type: application/json" \
  -d '{
    "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
    "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
    "k": [
      {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
      {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"}
    ],
    "transactions": [
      {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
      {"date": "2023-02-28 15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
      {"date": "2023-07-01 21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
      {"date": "2023-12-17 08:09:00", "amount": 480, "ceiling": 500, "remanent": 20}
    ]
  }'
```

### 4. NPS Returns
```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:nps \
  -H "Content-Type: application/json" \
  -d '{
    "age": 29, "wage": 50000, "inflation": 5.5,
    "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
    "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
    "k": [
      {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:00"},
      {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"}
    ],
    "transactions": [
      {"date": "2023-10-12 20:15:00", "amount": 250},
      {"date": "2023-02-28 15:49:00", "amount": 375},
      {"date": "2023-07-01 21:59:00", "amount": 620},
      {"date": "2023-12-17 08:09:00", "amount": 480}
    ]
  }'
```

### 5. Index Fund Returns
```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:index \
  -H "Content-Type: application/json" \
  -d '{ ... same as NPS ... }'
```

### 6. Performance
```bash
curl http://localhost:5477/blackrock/challenge/v1/performance
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5477` | Backend port |
| `WORKERS` | `4` | Uvicorn worker count |
| `ENV` | `development` | Environment mode |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Pydantic v2, uvicorn |
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Zustand |
| Infrastructure | Docker, Docker Compose, Nginx |
| Testing | pytest, httpx, pytest-asyncio |
