from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes.health import router as health_router
from routes.onboarding import router as onboarding_router
from routes.goals import router as goals_router
from routes.profile import router as profile_router

app = FastAPI(title="Aura API")

# Dev-only CORS: allow Vite dev server.
# Make this env-variable-driven before any deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(onboarding_router)
app.include_router(goals_router)
app.include_router(profile_router)


@app.on_event("startup")
def on_startup():
    init_db()
