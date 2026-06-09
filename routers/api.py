from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Product, Order, OrderItem
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api")


class CartItem(BaseModel):
    product_id: int
    quantity: int


class CheckoutData(BaseModel):
    customer_name: str
    phone: str
    address: str
    comment: Optional[str] = ""
    items: List[CartItem]


@router.get("/products")
async def get_products(category: int = None, search: str = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category_id == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    products = query.order_by(Product.created_at.desc()).all()
    return [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "old_price": p.old_price,
        "image": p.image,
        "stock": p.stock,
        "category_id": p.category_id,
        "is_featured": p.is_featured
    } for p in products]


@router.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse({"error": "Product not found"}, status_code=404)
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "old_price": product.old_price,
        "image": product.image,
        "stock": product.stock,
        "category_id": product.category_id
    }


@router.post("/checkout")
async def checkout(data: CheckoutData, db: Session = Depends(get_db)):
    if not data.items:
        return JSONResponse({"error": "Savat bo'sh!"}, status_code=400)

    total = 0
    order_items = []

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            return JSONResponse({"error": f"Tovar topilmadi: ID {item.product_id}"}, status_code=400)
        if product.stock < item.quantity:
            return JSONResponse({"error": f"'{product.name}' yetarli emas. Qolgan: {product.stock}"}, status_code=400)

        item_total = product.price * item.quantity
        total += item_total
        order_items.append(OrderItem(
            product_id=product.id,
            product_name=product.name,
            quantity=item.quantity,
            price=product.price
        ))
        product.stock -= item.quantity

    order = Order(
        customer_name=data.customer_name,
        phone=data.phone,
        address=data.address,
        comment=data.comment or "",
        total=total
    )
    db.add(order)
    db.flush()

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    db.commit()
    return {"success": True, "order_id": order.id, "total": total}


@router.get("/track/{phone}")
async def track_order(phone: str, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.phone == phone).order_by(Order.created_at.desc()).all()
    if not orders:
        return JSONResponse({"error": "Buyurtma topilmadi"}, status_code=404)
    return [{
        "id": o.id,
        "total": o.total,
        "status": o.status,
        "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
        "items": [{
            "name": i.product_name,
            "quantity": i.quantity,
            "price": i.price
        } for i in o.items]
    } for o in orders]
