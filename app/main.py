from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.links import categories_router, router as links_router
from app.api.schemas.links import LinkCategory
from app.crud.categories import seed_categories
from app.db import create_db_tables, engine
from app.models.category import CategoryRecord  # noqa: F401 — ensures table is created


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    from sqlmodel import Session
    with Session(engine) as session:
        seed_categories(session, [cat.value for cat in LinkCategory])
    yield


app = FastAPI(title="Link Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(links_router)
app.include_router(categories_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
