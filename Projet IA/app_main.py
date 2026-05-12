import os
import csv
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

app = FastAPI(
    title="SCCT - Supply Chain App",
    version="2.0",
    description="Application logistique utilisateur (Microservice App)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

def _get_html(filename: str) -> HTMLResponse:
    path = os.path.join("static", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content=f"<h1>Erreur 404</h1>", status_code=404)

@app.get("/", response_class=HTMLResponse)
async def root(): return _get_html("index.html")

@app.get("/app", response_class=HTMLResponse)
async def app_page(): return _get_html("app.html")

@app.get("/home", response_class=HTMLResponse)
async def home_page(): return _get_html("home.html")

@app.get("/health")
async def health():
    return {"status": "online", "service": "SCCT-Business", "timestamp": datetime.now().isoformat()}

# ══════════════════════════════════════════════════════════════════════════
# LOGGING SYSTEM (Data collection for retraining)
# ══════════════════════════════════════════════════════════════════════════

LOG_FILE = "navigation_logs.csv"

def log_navigation(user_action: str, url: str, verdict: str):
    """Enregistre le trafic et les connexions en base CSV pour futur ré-entraînement."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Action", "URL", "Decision_NIDS"])
        writer.writerow([datetime.now().isoformat(), user_action, url, verdict])

# ══════════════════════════════════════════════════════════════════════════
# BUSINESS LOGIC (Calls Admin NIDS API secretly on port 9000)
# ══════════════════════════════════════════════════════════════════════════

ADMIN_API_URL = "http://127.0.0.1:9000/predict"

async def check_security(flow_data: dict, action: str, url: str = "") -> bool:
    flow_data['url'] = url
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(ADMIN_API_URL, json=flow_data, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                verdict = data.get("verdict", "ALLOW")
                log_navigation(action, url, verdict)
                return verdict == "ALLOW"
    except Exception as e:
        print(f"Erreur de communication avec le NIDS Admin: {e}")
        log_navigation(action, url, "ERROR")
        return True # Fail-open si le NIDS est down
    return True

class LoginReq(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def login(req: LoginReq):
    # Flux très calme pour le login (Normal)
    flow = {"dur":0.5, "rate":2, "sbytes":120, "dbytes":120, "sttl":64, "dttl":64}
    is_safe = await check_security(flow, "LOGIN", "")
    if not is_safe:
        raise HTTPException(status_code=403, detail="Service indisponible temporairement.") # Invisible error
        
    if req.username == "admin" and req.password == "admin":
        return {"access_token": "mock-jwt-token-12345", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Identifiants incorrects")

@app.post("/api/business/deliveries")
async def create_delivery(req: Request):
    flow = {"dur":0.1, "rate":50, "sbytes":500, "dbytes":300}
    is_safe = await check_security(flow, "CREATE_DELIVERY", "")
    if not is_safe:
        raise HTTPException(status_code=403, detail="Opération annulée par le système.")
    return {"status": "created"}

@app.post("/api/business/external_monitor")
async def monitor_external(req: Request):
    data = await req.json()
    url = data.get("url", "")
    
    # Attack pattern if hacking attempt
    if ".xyz" in url or "hacker" in url:
        flow = {"dur":0.001, "rate":9000, "sbytes":10000, "dbytes":0}
    else:
        flow = {"dur":0.2, "rate":15, "sbytes":600, "dbytes":400}
        
    is_safe = await check_security(flow, "EXTERNAL_URL_CHECK", url)
    if not is_safe:
        raise HTTPException(status_code=403, detail="Cette URL a été bloquée car le domaine est inaccessible ou non sécurisé.")
    return {"status": "monitored", "url": url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
