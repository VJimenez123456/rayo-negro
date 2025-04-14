from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationSchema(BaseModel):
    id: int
    name: str
    address1: Optional[str]
    address2: Optional[str]
    city: str
    zip: Optional[str]
    province: Optional[str]
    country: str
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    country_code: str
    country_name: str
    province_code: Optional[str]
    legacy: bool
    active: bool
    admin_graphql_api_id: str


class DeleteLocationSchema(BaseModel):
    id: int
