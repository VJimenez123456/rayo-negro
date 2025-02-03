from pydantic import BaseModel
from datetime import datetime


class InventorySchema(BaseModel):
    inventory_item_id: int
    location_id: int
    available: int
    updated_at: datetime
    admin_graphql_api_id: str
