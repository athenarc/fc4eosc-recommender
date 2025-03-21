import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from darelabdb.api_faircore_mabrecs.apis import datadazzle, faircore
from darelabdb.api_faircore_mabrecs.readis import Readis
from darelabdb.utils_configs.apis.faircore_mabrecs import settings
from darelabdb.utils_configs.apis.datadazzle_mabrecs import (
    settings as settings_datadazzle,
)

if "DEV" not in os.environ:  # pragma: no cover
    sentry_sdk.init(
        dsn=os.getenv("MABRECS_SENTRY", ""),
        traces_sample_rate=0.1,
        _experiments={
            "profiles_sample_rate": 0.1,
        },
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before
    # initialize readis for faircore
    readis = Readis(settings.redis)
    await readis.initialize(settings.production_dir)

    # initialize readis for datadazzle
    readis2 = Readis(settings_datadazzle.redis)
    await readis2.initialize(settings_datadazzle.production_dir)
    yield
    # after


app = FastAPI(
    openapi_url=settings.base_path + "/openapi.json",
    docs_url=settings.base_path + "/docs",
    redoc_url=settings.base_path + "/redoc",
    lifespan=lifespan,
)

app.include_router(faircore.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API FOR DATADAZZLE


subapi = FastAPI(
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

subapi.include_router(datadazzle.router)


subapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@subapi.get("/sentry-debug")
async def trigger_error():  # pragma: no cover
    division_by_zero = 1 / 0


app.mount(settings_datadazzle.base_path, subapi)
