import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import event_types, moderation, reports, stations, users
from app.services.expiry import run_expiry_loop

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    expiry_task = asyncio.create_task(run_expiry_loop())
    yield
    expiry_task.cancel()
    try:
        await expiry_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="FuelWatch API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_v1_prefix
app.include_router(users.router, prefix=prefix)
app.include_router(event_types.router, prefix=prefix)
app.include_router(reports.router, prefix=prefix)
app.include_router(stations.router, prefix=prefix)
app.include_router(moderation.router, prefix=prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}