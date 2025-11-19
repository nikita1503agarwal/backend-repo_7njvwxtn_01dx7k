import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
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


# ---------------------- AUTH ----------------------
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "F0r3St12!")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "F0r3St12!")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "forest-admin-token-001")

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str

@app.post("/api/login", response_model=LoginResponse)
def admin_login(payload: LoginRequest):
    if payload.username == ADMIN_USERNAME and payload.password == ADMIN_PASSWORD:
        return {"token": ADMIN_TOKEN}
    raise HTTPException(status_code=401, detail="Invalid credentials")


def require_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


# ---------------------- MODELS ----------------------
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

# Product and Category payloads
class ProductIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image: Optional[str] = None
    badge: Optional[str] = None
    in_stock: bool = True

class ProductOut(ProductIn):
    id: str

class CategoryIn(BaseModel):
    name: str
    slug: str
    image: Optional[str] = None

class CategoryOut(CategoryIn):
    id: str

# Content update payload
class UpdateContentRequest(BaseModel):
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_cta_text: Optional[str] = None
    hero_secondary_cta_text: Optional[str] = None
    hero_badges: Optional[List[str]] = None
    hero_image: Optional[str] = None
    spline_url: Optional[str] = None
    shop_title: Optional[str] = None
    shop_subtitle: Optional[str] = None
    trust_items: Optional[List[dict]] = None
    testimonials: Optional[List[dict]] = None


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
        # Seed default content document if none exists
        content_count = db["content"].count_documents({})
        if content_count == 0:
            default_content = {
                "hero_title": "Wellness from the Forest",
                "hero_subtitle": "Pure, eco-friendly goods crafted with care. Fresh, holistic, and delightfully simple for everyday vitality.",
                "hero_cta_text": "Order Online",
                "hero_secondary_cta_text": "Our Promise",
                "hero_badges": [
                    "• Certified organic",
                    "• Plastic-free shipping",
                    "• 30-day happiness guarantee",
                ],
                "hero_image": None,
                "spline_url": None,
                "shop_title": "Shop popular picks",
                "shop_subtitle": "Nature-made • Lab-tested • Planet-kind",
                "trust_items": [
                    {"icon": "Leaf", "title": "Organic & Pure", "text": "Sourced from trusted growers"},
                    {"icon": "ShieldCheck", "title": "Quality Assured", "text": "Third‑party tested"},
                    {"icon": "Truck", "title": "Fast, Eco Shipping", "text": "Carbon‑aware logistics"},
                    {"icon": "HandHeart", "title": "Giveback", "text": "1% to reforestation"},
                ],
                "testimonials": [
                    {"quote": "The flavors are fresh and the ritual calms me.", "author": "Mara L.", "role": "Designer"},
                    {"quote": "Feels premium without being wasteful.", "author": "Ravi P.", "role": "Trainer"},
                    {"quote": "Love the soft, modern vibe and quality.", "author": "Jules K.", "role": "Nutritionist"},
                ],
            }
            create_document("content", default_content)
    except Exception:
        pass


@app.on_event("startup")
async def on_startup():
    seed_products_if_needed()


# ---------------------- PRODUCTS ----------------------
@app.get("/api/products")
def list_products():
    if db is None:
        # fallback to sample
        return SAMPLE_PRODUCTS
    products = get_documents("product")
    # Convert ObjectId to string if present
    normalized = []
    for p in products:
        if isinstance(p.get("_id"), ObjectId):
            p["id"] = str(p["_id"])
            del p["_id"]
        normalized.append(p)
    return normalized


@app.post("/api/products", dependencies=[Depends(require_admin)])
def create_product(payload: ProductIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    pid = create_document("product", payload.model_dump())
    doc = db["product"].find_one({"_id": ObjectId(pid)})
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.put("/api/products/{product_id}", dependencies=[Depends(require_admin)])
def update_product(product_id: str, payload: ProductIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    db["product"].update_one({"_id": oid}, {"$set": payload.model_dump()})
    doc = db["product"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.delete("/api/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    res = db["product"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}


# ---------------------- CATEGORIES ----------------------
@app.get("/api/categories")
def list_categories():
    if db is None:
        return []
    cats = get_documents("category")
    out = []
    for c in cats:
        if isinstance(c.get("_id"), ObjectId):
            c["id"] = str(c.pop("_id"))
        out.append(c)
    return out


@app.post("/api/categories", dependencies=[Depends(require_admin)])
def create_category(payload: CategoryIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    cid = create_document("category", payload.model_dump())
    doc = db["category"].find_one({"_id": ObjectId(cid)})
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.put("/api/categories/{category_id}", dependencies=[Depends(require_admin)])
def update_category(category_id: str, payload: CategoryIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        oid = ObjectId(category_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid category id")
    db["category"].update_one({"_id": oid}, {"$set": payload.model_dump()})
    doc = db["category"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Category not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.delete("/api/categories/{category_id}", dependencies=[Depends(require_admin)])
def delete_category(category_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        oid = ObjectId(category_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid category id")
    res = db["category"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"ok": True}


# ---------------------- CONTENT ----------------------
@app.get("/api/content")
def get_content():
    """Fetch the single editable site content document"""
    if db is None:
        # Fallback minimal content
        return {
            "hero_title": "Wellness from the Forest",
            "hero_subtitle": "Pure, eco-friendly goods crafted with care.",
            "hero_cta_text": "Order Online",
            "hero_secondary_cta_text": "Our Promise",
            "hero_badges": ["• Certified organic", "• Plastic-free shipping", "• 30-day happiness guarantee"],
            "hero_image": None,
            "spline_url": None,
            "shop_title": "Shop popular picks",
            "shop_subtitle": "Nature-made • Lab-tested • Planet-kind",
            "trust_items": [],
            "testimonials": [],
        }
    doc = db["content"].find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.put("/api/content", dependencies=[Depends(require_admin)])
def update_content(payload: UpdateContentRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["content"].find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    db["content"].update_one({"_id": doc["_id"]}, {"$set": updates})
    new_doc = db["content"].find_one({"_id": doc["_id"]})
    new_doc["id"] = str(new_doc.pop("_id"))
    return new_doc


# ---------------------- CHECKOUT ----------------------
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
            # try to find by id directly
            try:
                prod = db["product"].find_one({"_id": ObjectId(it.product_id)}) if db is not None else None
            except Exception:
                prod = None
        if prod is None:
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
