from fastapi import APIRouter, Request, Response, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.auth import create_access_token

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    # Check if already logged in by looking for cookie
    token = request.cookies.get("session_token")
    if token:
        # verify token logic...
        pass
    
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.post("/login")
async def process_login(request: Request, response: Response, password: str = Form(...)):
    if password == settings.app_password:
        access_token = create_access_token(data={"sub": "admin"})
        # 30 days expiry cookie
        max_age = settings.session_expiry_days * 24 * 60 * 60
        redirect = RedirectResponse(url="/fraud-check", status_code=303)
        redirect.set_cookie(key="session_token", value=access_token, httponly=True, max_age=max_age)
        return redirect
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password!"}, status_code=401)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_token")
    return response
