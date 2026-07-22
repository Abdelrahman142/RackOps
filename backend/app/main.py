from fastapi import FastAPI

from app.core.config import settings
from app.api.v1 import auth as auth_v1
from app.api.v1 import company as company_v1
from app.api.v1 import users as users_v1
from app.api.v1 import datacenters as datacenters_v1
from app.api.v1 import buildings as buildings_v1
from app.api.v1 import floors as floors_v1
from app.api.v1 import rooms as rooms_v1
from app.api.v1 import racks as racks_v1
from app.api.v1 import devices as devices_v1
from app.api.v1 import power as power_v1
from app.api.v1 import cooling as cooling_v1
from app.api.v1 import network as network_v1
from app.api.v1 import monitoring as monitoring_v1
from app.api.v1 import alerting as alerting_v1
from app.api.v1 import dashboard as dashboard_v1
from app.api.v1 import automation as automation_v1

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(
    auth_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    company_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    users_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    datacenters_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    buildings_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    floors_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    rooms_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    racks_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    devices_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    power_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    cooling_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    network_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    monitoring_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    alerting_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    dashboard_v1.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    automation_v1.router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/")
def home():
    return {"message": "RackOps is running"}
