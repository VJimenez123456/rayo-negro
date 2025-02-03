from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationSchema(BaseModel):
    id: int
    name: str
    address1: str
    address2: Optional[str] = None
    city: str
    zip: Optional[str] = None
    province: str
    country: str
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    country_code: str
    country_name: str
    province_code: Optional[str] = None
    legacy: bool
    active: bool
    admin_graphql_api_id: str


class DeleteLocationSchema(BaseModel):
    id: int
