# Build: docker build -t blk-hacking-ind-narender .
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.gzip import GZipMiddleware
from core.middleware import TimingMiddleware
from routers import transactions, returns, performance

app = FastAPI(
    title="BlackRock Auto-Savings API",
    version="1.0.0",
    description="Production-grade API for automated retirement savings through expense-based micro-investments.",
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=ORJSONResponse,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/blackrock/challenge/v1")
app.include_router(returns.router, prefix="/blackrock/challenge/v1")
app.include_router(performance.router, prefix="/blackrock/challenge/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
