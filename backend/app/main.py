from fastapi import FastAPI
from app.routes import decision
from app.config import settings

app = FastAPI(title="StackDecide Backend")

app.include_router(decision.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
