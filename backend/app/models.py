from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List

class LeadCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=30, description="Instagram username of target lead")
    niche: str = Field("Fashion Wear", description="B2B niche, e.g., Martial Arts, Fashion Wear")
    status: Optional[str] = "Pending"

class AccountCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    password: str = Field(..., description="Encrypted/stored credentials securely")
    proxy: Optional[str] = Field(None, description="Optional custom proxy URL e.g. http://user:pass@ip:port")

class SettingsUpdate(BaseModel):
    campaign_name: str
    dm_template: str
    comment_template: str
    safety_warmup_mode: bool
    max_leads_per_day: int

class GenerateMessageRequest(BaseModel):
    username: str
    niche: str
    custom_instructions: Optional[str] = None

class LeadStatusUpdate(BaseModel):
    lead_id: str
    status: str
