from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Any


class ShippingAddress(BaseModel):
    first_name: str
    last_name: str
    name: str
    address1: str
    address2: Optional[str] = None
    phone: str
    city: str
    zip: str
    province: str
    country: str
    country_code: str
    province_code: str
    company: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Address(BaseModel):
    id: int
    customer_id: int
    first_name: str
    last_name: str
    company: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    province: str
    country: str
    zip: str
    phone: Optional[str] = None
    name: str
    province_code: str
    country_code: str
    country_name: str
    default: bool


class Customer(BaseModel):
    id: int
    email: str
    created_at: datetime
    updated_at: datetime
    first_name: str
    last_name: str
    state: str
    note: Optional[str] = None
    verified_email: bool
    multipass_identifier: Optional[str] = None
    tax_exempt: bool
    phone: Optional[str] = None
    currency: str
    tax_exemptions: List[str]
    admin_graphql_api_id: str
    default_address: Address


class OrderSchema(BaseModel):
    id: int
    created_at: str
    financial_status: Optional[str]
    fulfillment_status: Optional[Any]
    note: Optional[Any]
    order_number: int
    tags: Optional[str]
    total_price: Optional[str]
    customer: Optional[Customer]
    shipping_address: Optional[ShippingAddress]
