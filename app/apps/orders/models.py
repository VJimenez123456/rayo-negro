from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Any


class ShippingAddress(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    province_code: Optional[str] = None
    company: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Address(BaseModel):
    id: Optional[int] = None
    customer_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    province_code: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    default: bool


class Customer(BaseModel):
    id: int
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    state: str
    note: Optional[str] = None
    verified_email: bool
    multipass_identifier: Optional[str] = None
    tax_exempt: bool
    phone: Optional[str] = None
    currency: str
    tax_exemptions: List[str]
    admin_graphql_api_id: str
    default_address: Optional[Address] = None


class LineItem(BaseModel):
    id: int
    # admin_graphql_api_id: str
    # attributed_staffs: List[Any]
    # current_quantity: int
    # fulfillable_quantity: int
    # fulfillment_service: str
    # fulfillment_status: Optional[str]
    # gift_card: bool
    # grams: int
    # name: str
    price: str
    # price_set: Optional[Any]
    # product_exists: bool
    product_id: str | int | None
    # properties: List[Any]
    quantity: int
    # requires_shipping: bool
    # sales_line_item_group_id: Optional[Any]
    sku: str | int | None
    # taxable: bool
    title: str
    # total_discount: str
    # total_discount_set: Optional[Any]
    variant_id: str | int | None
    # variant_inventory_management: Optional[str]
    # variant_title: Optional[str]
    # vendor: str
    # tax_lines: List[Any]
    # duties: List[Any]
    # discount_allocations: List[Any]


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
    cancelled_at: Optional[Any]
    closed_at: Optional[Any]
    line_items: List[LineItem]
