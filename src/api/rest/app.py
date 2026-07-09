from fastapi import FastAPI

from src.api.rest.middleware.cors import setup_cors
from src.api.rest.routes import health, sse, websocket
from src.api.rest.routes.identity_routes import admin_route, auth_route, mentor_route
from src.api.rest.routes.space_node_routes import node_route, space_route

app = FastAPI(title="Identity Service")

setup_cors(app)

app.include_router(health.router)
app.include_router(auth_route.router)
app.include_router(admin_route.router)
app.include_router(mentor_route.router)
app.include_router(mentor_route.profile_router)
app.include_router(space_route.router)
app.include_router(node_route.router)
app.include_router(sse.router)
app.include_router(websocket.router)
