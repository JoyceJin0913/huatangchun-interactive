from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import novel, interactive, room
from database import init_db

app = FastAPI(title="互动文游 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(novel.router)
app.include_router(interactive.router)
app.include_router(room.router)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
