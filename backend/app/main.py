from fastapi import FastAPI
from app.routes import decision, settings as settings_route
from app.config import settings

app = FastAPI(title="StackDecide Backend")

app.include_router(decision.router)
app.include_router(settings_route.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
