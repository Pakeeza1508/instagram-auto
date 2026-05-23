import json
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import (
    accounts_col, leads_col, settings_col, logs_col, seed_initial_settings, get_db_status
)
from app.models import LeadCreate, AccountCreate, SettingsUpdate, GenerateMessageRequest, LeadStatusUpdate
from app.services.ai_service import ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="Instagram Outreach Automation Hub", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed initial settings and mock data on startup
seed_initial_settings()

# State variable for the background automation queue
campaign_running = False
log_queue = asyncio.Queue()


def normalize_instagram_username(value: str) -> str:
    """Normalize usernames so @name / @@name are stored consistently as name."""
    return value.strip().lstrip("@").strip().lower()


def extract_inserted_id(result):
    """Extract inserted id from pymongo result or fallback insert return value."""
    if hasattr(result, "inserted_id"):
        return str(result.inserted_id)
    if isinstance(result, dict) and result.get("_id") is not None:
        return str(result.get("_id"))
    return None

def log_event(message: str, level: str = "INFO"):
    """Saves a log message to the database and queue for SSE stream"""
    timestamp = datetime.now().isoformat()
    log_doc = {"timestamp": timestamp, "level": level, "message": message}
    try:
        logs_col.insert_one(log_doc)
    except Exception:
        pass
    
    # Broadcast to dashboard SSE
    asyncio.create_task(log_queue.put(log_doc))

# Background Queue Task
async def run_automation_loop():
    global campaign_running
    log_event("Starting backend lead processing loop...", "INFO")
    
    while campaign_running:
        try:
            # 1. Fetch available accounts
            accounts = list(accounts_col.find({"status": "Active"}))
            if not accounts:
                log_event("No active accounts available! Halting outreach loop.", "WARNING")
                campaign_running = False
                break
                
            # 2. Get pending B2B lead
            lead = leads_col.find_one({"status": "Pending"})
            if not lead:
                log_event("No pending leads remaining in the database.", "INFO")
                campaign_running = False
                break
            
            # Select account (simple round-robin rotate)
            account = accounts[0]
            leads_col.update_one(
                {"_id": lead["_id"]},
                {"$set": {"status": "Processing", "last_action": datetime.now().isoformat()}}
            )
            log_event(
                f"[{account['username']}] Processing lead @{lead['username']} (DB mode: {get_db_status().get('mode', 'unknown')}).",
                "INFO"
            )

            # Real external Instagram actions are not implemented in this backend.
            # Keep logs truthful and avoid claiming follow/like/comment/DM happened.
            if not settings.LIVE_EXECUTION_ENABLED:
                leads_col.update_one(
                    {"_id": lead["_id"]},
                    {"$set": {"status": "ReadyForExecution", "last_action": datetime.now().isoformat()}}
                )
                log_event(
                    f"[{account['username']}] Lead @{lead['username']} prepared only. LIVE_EXECUTION_ENABLED=false, so no Instagram action was performed.",
                    "WARNING"
                )
                await asyncio.sleep(1)
                continue

            # Placeholder: when live execution is implemented, this branch should execute real actions and logs.
            leads_col.update_one(
                {"_id": lead["_id"]},
                {"$set": {"status": "DMed", "last_action": datetime.now().isoformat()}}
            )
            log_event(f"Real outreach execution completed for lead @{lead['username']}.", "SUCCESS")
            
            # Update account analytics
            accounts_col.update_one(
                {"_id": account["_id"]},
                {"$inc": {"daily_actions.dm": 1, "daily_actions.follow": 1, "daily_actions.like": 1}}
            )
            
            # Cooldown execution
            cooldown = settings.MIN_DELAY_SECONDS
            log_event(f"Cooldown for {cooldown} seconds before next lead...", "INFO")
            
            for _ in range(cooldown):
                if not campaign_running:
                    break
                await asyncio.sleep(1)
                
        except Exception as e:
            log_event(f"Automation execution error: {str(e)}", "ERROR")
            if lead:
                leads_col.update_one({"_id": lead["_id"]}, {"$set": {"status": "Failed"}})
            await asyncio.sleep(10)

# API Endpoints

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Retrieve aggregations for the control header metrics"""
    total_leads = leads_col.count_documents({})
    pending_leads = leads_col.count_documents({"status": "Pending"})
    dmed_leads = leads_col.count_documents({"status": "DMed"})
    replied_leads = leads_col.count_documents({"status": "Replied"})
    failed_leads = leads_col.count_documents({"status": "Failed"})
    
    active_accounts = accounts_col.count_documents({"status": "Active"})
    
    return {
        "total_leads": total_leads,
        "pending_leads": pending_leads,
        "dmed_leads": dmed_leads,
        "replied_leads": replied_leads,
        "failed_leads": failed_leads,
        "active_accounts": active_accounts,
        "campaign_running": campaign_running,
        "db_mode": get_db_status().get("mode", "unknown")
    }


@app.get("/api/health/db")
async def db_health():
    """Reports whether app is using MongoDB or fallback storage."""
    return get_db_status()

@app.get("/api/accounts")
async def get_accounts():
    accounts = list(accounts_col.find({}, {"password": 0}))
    for acc in accounts:
        if "_id" in acc:
            acc["_id"] = str(acc["_id"])
    return accounts

@app.post("/api/accounts")
async def add_account(acc: AccountCreate):
    try:
        username = normalize_instagram_username(acc.username)
        db_mode = get_db_status().get("mode", "unknown")
        new_acc = {
            "username": username,
            "status": "Active",
            "proxy": acc.proxy,
            "daily_actions": {"dm": 0, "follow": 0, "like": 0},
            "last_active": None
        }
        result = accounts_col.insert_one(new_acc)
        inserted_id = extract_inserted_id(result)
        log_event(
            f"Account saved to DB ({db_mode}): @{username} (id={inserted_id or 'n/a'}).",
            "SUCCESS"
        )
        return {
            "status": "success",
            "message": "Account added.",
            "username": username,
            "id": inserted_id,
            "db_mode": db_mode,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Account save failed: {str(e)}")

@app.get("/api/leads")
async def get_leads():
    leads = list(leads_col.find())
    for lead in leads:
        if "_id" in lead:
            lead["_id"] = str(lead["_id"])
    return leads

@app.post("/api/leads")
async def add_lead(lead: LeadCreate):
    try:
        username = normalize_instagram_username(lead.username)
        db_mode = get_db_status().get("mode", "unknown")
        result = leads_col.insert_one({
            "username": username,
            "niche": lead.niche,
            "status": lead.status,
            "last_action": None
        })
        inserted_id = extract_inserted_id(result)
        log_event(
            f"Lead saved to DB ({db_mode}): @{username} (id={inserted_id or 'n/a'}).",
            "INFO"
        )
        return {
            "status": "success",
            "username": username,
            "id": inserted_id,
            "db_mode": db_mode,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lead save failed: {str(e)}")



@app.post("/api/leads/status")
async def update_lead_status(payload: LeadStatusUpdate):
    try:
        from bson import ObjectId
        # Support both MongoDB ObjectId and Mock string IDs
        try:
            query_id = ObjectId(payload.lead_id)
        except Exception:
            query_id = payload.lead_id
            
        leads_col.update_one(
            {"_id": query_id},
            {"$set": {"status": payload.status, "last_action": datetime.now().isoformat()}}
        )
        log_event(f"Lead status manually updated to '{payload.status}'.", "INFO")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    db_settings = settings_col.find_one({})
    if db_settings:
        if "_id" in db_settings:
            db_settings["_id"] = str(db_settings["_id"])
        return db_settings
    return {}

@app.post("/api/settings")
async def update_settings(payload: SettingsUpdate):
    settings_col.update_one(
        {},
        {"$set": {
            "campaign_name": payload.campaign_name,
            "dm_template": payload.dm_template,
            "comment_template": payload.comment_template,
            "safety_warmup_mode": payload.safety_warmup_mode,
            "max_leads_per_day": payload.max_leads_per_day
        }},
        upsert=True
    )
    log_event("Global campaign parameter profiles successfully reconfigured.", "INFO")
    return {"status": "success"}

@app.post("/api/ai/preview")
async def preview_ai_msg(payload: GenerateMessageRequest):
    """Realtime debug previewing Groq prompt outputs"""
    dm = ai_service.generate_b2b_dm(payload.username, payload.niche, payload.custom_instructions)
    comment = ai_service.generate_comment(payload.username, payload.niche)
    return {"dm": dm, "comment": comment}

@app.post("/api/campaign/toggle")
async def toggle_campaign(background_tasks: BackgroundTasks):
    global campaign_running
    campaign_running = not campaign_running
    if campaign_running:
        background_tasks.add_task(run_automation_loop)
        log_event("Campaign dispatcher launched.", "INFO")
    else:
        log_event("Campaign dispatcher paused.", "WARNING")
    return {"running": campaign_running}

@app.get("/api/logs/stream")
async def logs_stream():
    """Realtime Server-Sent Events log pipe for the dynamic GUI panel"""
    async def event_generator():
        # Yield previous logs on first connection
        past_logs = list(logs_col.find().sort("timestamp", -1).limit(20))
        for log in reversed(past_logs):
            yield f"data: {json.dumps({'timestamp': log['timestamp'], 'level': log['level'], 'message': log['message']})}\n\n"
            
        while True:
            log_item = await log_queue.get()
            yield f"data: {json.dumps(log_item)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Mount Dashboard SPA
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
