import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import db, create_document, get_documents
from schemas import Restaurant, Dish, Order

app = FastAPI(title="Food Delivery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Food Delivery API is running"}

@app.get("/schema")
def get_schema_defs():
    # Let the database viewer discover schemas
    return {
        "schemas": [
            "restaurant",
            "dish",
            "order"
        ]
    }

# Seed data endpoint (idempotent-ish)
@app.post("/seed")
def seed_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Check if restaurants already exist
    existing = db["restaurant"].count_documents({})
    if existing > 0:
        return {"status": "ok", "message": "Data already seeded"}

    restaurants = [
        Restaurant(
            name="Saffron Garden",
            description="Modern Indian plates with bold flavors",
            image_url="https://images.unsplash.com/photo-1604908176997-43162c1f66fb?q=80&w=2000&auto=format&fit=crop",
            cuisine="Indian",
            rating=4.7,
            delivery_time_min=25
        ),
        Restaurant(
            name="Toscana Rustica",
            description="Handmade pastas and wood‑fired pizza",
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=2000&auto=format&fit=crop",
            cuisine="Italian",
            rating=4.8,
            delivery_time_min=30
        ),
        Restaurant(
            name="Umami Wave",
            description="Ramen, sushi and small plates",
            image_url="https://images.unsplash.com/photo-1553621042-f6e147245754?q=80&w=2000&auto=format&fit=crop",
            cuisine="Japanese",
            rating=4.6,
            delivery_time_min=20
        ),
    ]

    for r in restaurants:
        rid = create_document("restaurant", r)
        # Create some dishes
        sample_dishes = [
            Dish(restaurant_id=rid, name="Butter Chicken", description="Creamy tomato sauce", price=14.5,
                 image_url="https://images.unsplash.com/photo-1625944524872-6d2a3dfcc5a7?q=80&w=1600&auto=format&fit=crop", spicy=True),
            Dish(restaurant_id=rid, name="Margherita Pizza", description="Tomato, mozzarella, basil", price=12,
                 image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=1600&auto=format&fit=crop", vegetarian=True),
            Dish(restaurant_id=rid, name="Tonkotsu Ramen", description="Pork broth, spring onion", price=13,
                 image_url="https://images.unsplash.com/photo-1604908554027-28e7b1d1b3c0?q=80&w=1600&auto=format&fit=crop"),
        ]
        for d in sample_dishes:
            create_document("dish", d)

    return {"status": "ok", "message": "Seeded restaurants and dishes"}

# Public API
@app.get("/restaurants")
def list_restaurants():
    data = get_documents("restaurant", limit=50)
    # Convert ObjectId to str for _id
    for item in data:
        item["id"] = str(item.pop("_id"))
    return data

@app.get("/restaurants/{restaurant_id}/dishes")
def list_dishes(restaurant_id: str):
    data = get_documents("dish", {"restaurant_id": restaurant_id}, limit=100)
    for item in data:
        item["id"] = str(item.pop("_id"))
    return data

class OrderRequest(BaseModel):
    restaurant_id: str
    items: List[dict]
    customer_name: str
    customer_email: str
    customer_address: str
    notes: str | None = None

@app.post("/orders")
def create_order(order: OrderRequest):
    # Basic pricing server-side (trust but verify)
    items = []
    subtotal = 0.0
    for it in order.items:
        price = float(it.get("price", 0))
        qty = int(it.get("quantity", 1))
        items.append({
            "dish_id": it.get("dish_id"),
            "name": it.get("name"),
            "price": price,
            "quantity": qty
        })
        subtotal += price * qty

    delivery_fee = 3.99 if subtotal < 35 else 0.0
    total = round(subtotal + delivery_fee, 2)

    doc = Order(
        restaurant_id=order.restaurant_id,
        items=items,  # type: ignore
        subtotal=round(subtotal, 2),
        delivery_fee=delivery_fee,
        total=total,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_address=order.customer_address,
        notes=order.notes
    )

    oid = create_document("order", doc)
    return {"status": "ok", "order_id": oid, "total": total}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
