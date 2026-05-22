from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.links import categories_router, router as links_router
from app.db import create_db_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield


app = FastAPI(title="Link Service", lifespan=lifespan)

app.include_router(links_router)
app.include_router(categories_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
