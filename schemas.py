"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# CMS schemas
class TrustItem(BaseModel):
    icon: Optional[str] = Field(None, description="Icon name from lucide-react (e.g., Leaf, Shield)")
    title: str
    text: str

class Testimonial(BaseModel):
    quote: str
    author: str
    role: Optional[str] = None

class Content(BaseModel):
    """
    Site content editable by admin through CMS
    Collection name: "content" (lowercase of class name)
    """
    hero_title: str = Field("Wellness from the Forest", description="Main headline text")
    hero_subtitle: str = Field(
        "Pure, eco-friendly goods crafted with care. Fresh, holistic, and delightfully simple for everyday vitality.",
        description="Supporting paragraph"
    )
    hero_cta_text: str = Field("Order Online", description="Primary CTA label")
    hero_secondary_cta_text: str = Field("Our Promise", description="Secondary CTA label")
    hero_badges: List[str] = Field(default_factory=lambda: [
        "• Certified organic",
        "• Plastic-free shipping",
        "• 30-day happiness guarantee",
    ])
    hero_image: Optional[HttpUrl] = Field(None, description="Optional hero image URL")
    spline_url: Optional[HttpUrl] = Field(None, description="Optional Spline 3D scene URL")

    trust_items: List[TrustItem] = Field(default_factory=lambda: [
        TrustItem(icon="Leaf", title="Organic & Pure", text="Sourced from trusted growers"),
        TrustItem(icon="ShieldCheck", title="Quality Assured", text="Third‑party tested"),
        TrustItem(icon="Truck", title="Fast, Eco Shipping", text="Carbon‑aware logistics"),
        TrustItem(icon="HandHeart", title="Giveback", text="1% to reforestation"),
    ])

    testimonials: List[Testimonial] = Field(default_factory=lambda: [
        Testimonial(quote="The flavors are fresh and the ritual calms me.", author="Mara L.", role="Designer"),
        Testimonial(quote="Feels premium without being wasteful.", author="Ravi P.", role="Trainer"),
        Testimonial(quote="Love the soft, modern vibe and quality.", author="Jules K.", role="Nutritionist"),
    ])

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
