from fastapi import FastAPI

from app.api.routes.links import router as links_router

app = FastAPI(title="Link Service")

app.include_router(links_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
