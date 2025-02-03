from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class MoneySet(BaseModel):
    shop_money: Dict[str, Any]
    presentment_money: Dict[str, Any]


class TaxLine(BaseModel):
    price: str
    rate: float
    title: str
    price_set: MoneySet
    channel_liable: bool


class LineItem(BaseModel):
    id: int
    admin_graphql_api_id: str
    attributed_staffs: List[Any]
    current_quantity: int
    fulfillable_quantity: int
    fulfillment_service: str
    fulfillment_status: Optional[str]
    gift_card: bool
    grams: int
    name: str
    price: str
    price_set: MoneySet
    product_exists: bool
    product_id: int
    properties: List[Any]
    quantity: int
    requires_shipping: bool
    sales_line_item_group_id: Optional[Any]
    sku: str
    taxable: bool
    title: str
    total_discount: str
    total_discount_set: MoneySet
    variant_id: int
    variant_inventory_management: str
    variant_title: Optional[str]
    vendor: str
    tax_lines: List[TaxLine]
    duties: List[Any]
    discount_allocations: List[Any]


class ClientDetails(BaseModel):
    accept_language: Optional[str]
    browser_height: Optional[int]
    browser_ip: str
    browser_width: Optional[int]
    session_hash: Optional[str]
    user_agent: str


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
    admin_graphql_api_id: str
    app_id: int
    browser_ip: Optional[str]
    buyer_accepts_marketing: bool
    cancel_reason: Optional[Any]
    cancelled_at: Optional[Any]
    cart_token: Optional[Any]
    checkout_id: int
    checkout_token: str
    client_details: ClientDetails
    closed_at: Optional[Any]
    confirmation_number: str
    confirmed: bool
    contact_email: Optional[str]
    created_at: str
    currency: str
    current_shipping_price_set: MoneySet
    current_subtotal_price: str
    current_subtotal_price_set: MoneySet
    current_total_additional_fees_set: Optional[Any]
    current_total_discounts: str
    current_total_discounts_set: MoneySet
    current_total_duties_set: Optional[Any]
    current_total_price: str
    current_total_price_set: MoneySet
    current_total_tax: str
    current_total_tax_set: MoneySet
    customer_locale: Optional[str]
    device_id: Optional[Any]
    discount_codes: List[Any]
    duties_included: bool
    email: str
    estimated_taxes: bool
    financial_status: Optional[str]
    fulfillment_status: Optional[Any]
    landing_site: Optional[Any]
    landing_site_ref: Optional[Any]
    location_id: Optional[int]
    merchant_business_entity_id: Optional[str]
    merchant_of_record_app_id: Optional[Any]
    name: str
    note: Optional[Any]
    note_attributes: List[Any]
    number: int
    order_number: int
    order_status_url: str
    original_total_additional_fees_set: Optional[Any]
    original_total_duties_set: Optional[Any]
    payment_gateway_names: List[str]
    phone: Optional[Any]
    po_number: Optional[Any]
    presentment_currency: str
    processed_at: datetime
    reference: Optional[Any]
    referring_site: Optional[Any]
    source_identifier: Optional[Any]
    source_name: str
    source_url: Optional[Any]
    subtotal_price: str
    subtotal_price_set: MoneySet
    tags: Optional[str]
    tax_exempt: bool
    tax_lines: List[TaxLine]
    taxes_included: bool
    test: bool
    token: str
    total_cash_rounding_payment_adjustment_set: MoneySet
    total_cash_rounding_refund_adjustment_set: MoneySet
    total_discounts: str
    total_discounts_set: MoneySet
    total_line_items_price: str
    total_line_items_price_set: MoneySet
    total_outstanding: str
    total_price: Optional[str]
    total_price_set: MoneySet
    total_shipping_price_set: MoneySet
    total_tax: str
    total_tax_set: MoneySet
    total_tip_received: str
    total_weight: int
    updated_at: datetime
    user_id: int
    billing_address: Optional[Any]
    customer: Optional[Customer]
    discount_applications: List[Any]
    fulfillments: List[Any]
    line_items: List[LineItem]
    payment_terms: Optional[Any]
    refunds: List[Any]
    shipping_address: Optional[ShippingAddress]
    shipping_lines: List[Any]
    returns: List[Any]
