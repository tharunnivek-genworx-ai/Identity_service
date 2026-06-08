from fastapi import FastAPI

from src.api.rest.middleware.cors import setup_cors
from src.api.rest.routes import admin_route, auth_route, health, sse, websocket

app = FastAPI(title="Identity Service")

setup_cors(app)

app.include_router(health.router)
app.include_router(auth_route.router)
app.include_router(admin_route.router)
app.include_router(sse.router)
app.include_router(websocket.router)
