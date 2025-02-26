from pydantic import BaseModel
from datetime import datetime


class InventorySchema(BaseModel):
    inventory_item_id: int
    location_id: int
    available: int
    updated_at: datetime
    admin_graphql_api_id: str


class InventoryObject(BaseModel):
    variant_id: int | str
    location_id: int | str
    barcode: int | str
    stock: int | str
