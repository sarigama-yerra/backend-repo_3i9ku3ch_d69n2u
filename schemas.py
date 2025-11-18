"""
Database Schemas for Food Delivery App

Each Pydantic model corresponds to a MongoDB collection.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Restaurant(BaseModel):
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Short description")
    image_url: Optional[str] = Field(None, description="Cover image URL")
    cuisine: Optional[str] = Field(None, description="Cuisine type, e.g., Italian")
    rating: Optional[float] = Field(4.6, ge=0, le=5)
    delivery_time_min: Optional[int] = Field(20, ge=5, le=120)

class Dish(BaseModel):
    restaurant_id: str = Field(..., description="ID of the restaurant this dish belongs to")
    name: str = Field(..., description="Dish name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in dollars")
    image_url: Optional[str] = Field(None, description="Image URL")
    spicy: Optional[bool] = Field(False, description="Whether the dish is spicy")
    vegetarian: Optional[bool] = Field(False, description="Vegetarian friendly")

class OrderItem(BaseModel):
    dish_id: str
    name: str
    price: float
    quantity: int = Field(1, ge=1)

class Order(BaseModel):
    restaurant_id: str
    items: List[OrderItem]
    subtotal: float
    delivery_fee: float
    total: float
    customer_name: str
    customer_email: str
    customer_address: str
    notes: Optional[str] = None
