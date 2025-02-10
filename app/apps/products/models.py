from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Union
from datetime import datetime


class Variant(BaseModel):
    admin_graphql_api_id: str
    barcode: Optional[str]
    compare_at_price: Optional[Union[str, float]]
    created_at: datetime
    id: int
    inventory_policy: str
    position: int
    price: Optional[Union[str, float]] = '0.00'
    product_id: int
    sku: Optional[str] = 'Unknown'
    taxable: bool
    title: str
    updated_at: datetime
    option1: Optional[str]
    option2: Optional[str]
    option3: Optional[str]
    image_id: Optional[Union[str, int]]
    inventory_item_id: int
    inventory_quantity: int
    old_inventory_quantity: int


class Option(BaseModel):
    name: str
    id: int
    product_id: int
    position: int
    values: List[str]


class Image(BaseModel):
    id: int
    product_id: int
    position: int
    created_at: datetime
    updated_at: datetime
    alt: Optional[str]
    width: int
    height: int
    src: Optional[str] = 'Unknown'
    variant_ids: List[int]
    admin_graphql_api_id: str


class MediaPreviewImage(BaseModel):
    width: int
    height: int
    src: HttpUrl
    status: str


class Media(BaseModel):
    id: int
    product_id: int
    position: int
    created_at: datetime
    updated_at: datetime
    alt: Optional[str]
    status: str
    media_content_type: str
    preview_image: MediaPreviewImage
    variant_ids: List[int]
    admin_graphql_api_id: str


class Category(BaseModel):
    admin_graphql_api_id: str
    name: str
    full_name: str


class VariantGID(BaseModel):
    admin_graphql_api_id: str
    updated_at: datetime


class ProductSchema(BaseModel):
    admin_graphql_api_id: str
    body_html: Optional[str]
    created_at: datetime
    handle: str
    id: int
    product_type: Optional[str]
    published_at: Optional[Union[str, None]]
    template_suffix: Optional[str]
    title: str
    updated_at: datetime
    vendor: Optional[str] = 'Unknown'
    status: str
    published_scope: str
    tags: Optional[str]
    variants: List[Variant]
    options: List[Option]
    images: List[Image]
    image: Optional[Image]
    media: Optional[List[Media]] = None
    variant_gids: Optional[List[VariantGID]] = None
    has_variants_that_requires_components: Optional[bool] = None
    category: Optional[Category] = None


class DeleteProductSchema(BaseModel):
    id: int
