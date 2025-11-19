import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Forest Health Goods API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CartItem(BaseModel):
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(ge=1, default=1)


class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: str
    city: str
    country: str
    postal_code: str


class CreateOrderRequest(BaseModel):
    items: List[CartItem]
    customer: CustomerInfo
    notes: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Forest Health Goods API running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


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
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
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

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Utility: seed products if collection empty
SAMPLE_PRODUCTS = [
    {
        "title": "Forest Greens Superfood Blend",
        "description": "Organic spirulina, chlorella, and wheatgrass for daily vitality.",
        "price": 24.99,
        "category": "supplements",
        "in_stock": True,
        "image": "/images/greens.jpg",
        "badge": "Best Seller"
    },
    {
        "title": "Herbal Calm Tea",
        "description": "Chamomile, lemon balm, and passionflower for gentle relaxation.",
        "price": 12.5,
        "category": "wellness",
        "in_stock": True,
        "image": "/images/tea.jpg",
        "badge": "Soothing"
    },
    {
        "title": "Bamboo Fiber Bottle",
        "description": "Eco-friendly reusable bottle with soft-touch finish.",
        "price": 18.0,
        "category": "eco",
        "in_stock": True,
        "image": "/images/bottle.jpg",
        "badge": "Eco Choice"
    },
    {
        "title": "Wild Berry Vitamin C",
        "description": "Naturally flavored chews for immune support.",
        "price": 14.0,
        "category": "supplements",
        "in_stock": True,
        "image": "/images/vitamin-c.jpg",
        "badge": "New"
    },
]


def seed_products_if_needed():
    try:
        if db is None:
            return
        count = db["product"].count_documents({})
        if count == 0:
            for p in SAMPLE_PRODUCTS:
                create_document("product", p)
    except Exception:
        pass


@app.on_event("startup")
async def on_startup():
    seed_products_if_needed()


@app.get("/api/products")
def list_products():
    if db is None:
        # fallback to sample
        return SAMPLE_PRODUCTS
    products = get_documents("product")
    # Convert ObjectId to string if present
    for p in products:
        if isinstance(p.get("_id"), ObjectId):
            p["id"] = str(p["_id"])
            del p["_id"]
    return products


@app.post("/api/checkout")
def create_order(payload: CreateOrderRequest):
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")

    # Resolve product pricing
    items_summary = []
    subtotal = 0.0

    # Fetch products by ids
    ids = []
    for it in payload.items:
        try:
            ids.append(ObjectId(it.product_id))
        except Exception:
            # if not a valid ObjectId, skip DB lookup and rely on FE data (fallback)
            pass

    product_map = {}
    if db is not None and ids:
        for doc in db["product"].find({"_id": {"$in": ids}}):
            product_map[str(doc["_id"])] = doc

    for it in payload.items:
        prod = product_map.get(it.product_id)
        if prod is None:
            # try to find by title match fallback
            prod = db["product"].find_one({"_id": ObjectId(it.product_id)}) if db is not None else None
        if prod is None:
            # last resort: can't price item
            raise HTTPException(status_code=400, detail=f"Product not found: {it.product_id}")
        price = float(prod.get("price", 0))
        line_total = price * it.quantity
        subtotal += line_total
        items_summary.append({
            "product_id": str(prod.get("_id", it.product_id)),
            "title": prod.get("title"),
            "price": price,
            "quantity": it.quantity,
            "line_total": round(line_total, 2)
        })

    shipping = 5.0 if subtotal < 50 else 0.0
    total = round(subtotal + shipping, 2)

    order_doc = {
        "items": items_summary,
        "customer": payload.customer.model_dump(),
        "notes": payload.notes,
        "subtotal": round(subtotal, 2),
        "shipping": shipping,
        "total": total,
        "status": "received",
    }

    order_id = None
    if db is not None:
        order_id = create_document("order", order_doc)

    return {"order_id": order_id, "total": total, "status": "received"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
