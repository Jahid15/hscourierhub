from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.database import db
import os
import asyncio
from app.tasks import daily_reset_loop

app = FastAPI(title="HelloSquare Courier Hub", docs_url="/docs", redoc_url=None)

# Include middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Connect to database on startup
@app.on_event("startup")
async def startup_event():
    db.connect()
    asyncio.create_task(daily_reset_loop())

@app.on_event("shutdown")
async def shutdown_event():
    db.disconnect()

from app.routers import auth_routes, fraud_routes, merchant_id_routes, parcel_routes, account_routes, webhook_routes
app.include_router(auth_routes.router)
app.include_router(fraud_routes.router)
app.include_router(merchant_id_routes.router)
app.include_router(parcel_routes.router)
app.include_router(account_routes.router)
app.include_router(webhook_routes.router)

# Basic HTML response for index
templates = Jinja2Templates(directory="app/templates")

from fastapi.responses import RedirectResponse

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return RedirectResponse(url="/fraud-check")

@app.get("/api-docs", response_class=HTMLResponse)
async def api_docs_page(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request, "title": "API Documentation"})
