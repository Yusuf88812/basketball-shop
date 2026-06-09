from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Product, Category, Order, OrderItem, Admin
from auth import hash_password, verify_password, create_session, get_admin_from_session, delete_session
import shutil
import os
import uuid

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(request: Request, db: Session):
    token = request.cookies.get("admin_session")
    if not token:
        return None
    return get_admin_from_session(token, db)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse("admin/login.html", {
            "request": request, "error": "Noto'g'ri login yoki parol!"
        })
    token = create_session(admin.id)
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie("admin_session", token, httponly=True, max_age=86400)
    return response


@router.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("admin_session")
    if token:
        delete_session(token)
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


# ─── DASHBOARD ───
@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    new_orders = db.query(Order).filter(Order.status == "new").count()
    total_revenue = db.query(func.sum(Order.total)).filter(Order.status == "delivered").scalar() or 0
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    low_stock = db.query(Product).filter(Product.stock <= 5).all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin": admin,
        "total_products": total_products,
        "total_orders": total_orders,
        "new_orders": new_orders,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "low_stock": low_stock
    })


# ─── CATEGORIES ───
@router.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    categories = db.query(Category).all()
    return templates.TemplateResponse("admin/categories.html", {
        "request": request, "admin": admin, "categories": categories
    })


@router.post("/categories/add")
async def add_category(request: Request, name: str = Form(...), icon: str = Form("🏀"),
                       description: str = Form(""), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    cat = Category(name=name, icon=icon, description=description)
    db.add(cat)
    db.commit()
    return RedirectResponse(url="/admin/categories", status_code=303)


@router.post("/categories/delete/{cat_id}")
async def delete_category(request: Request, cat_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse(url="/admin/categories", status_code=303)


# ─── PRODUCTS ───
@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    categories = db.query(Category).all()
    return templates.TemplateResponse("admin/products.html", {
        "request": request, "admin": admin, "products": products, "categories": categories
    })


@router.post("/products/add")
async def add_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    old_price: float = Form(None),
    stock: int = Form(0),
    category_id: int = Form(None),
    is_featured: bool = Form(False),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    image_path = "/static/uploads/default.png"
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = f"/static/uploads/{filename}"

    product = Product(
        name=name, description=description, price=price, old_price=old_price,
        stock=stock, category_id=category_id if category_id else None,
        is_featured=is_featured, image=image_path
    )
    db.add(product)
    db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


@router.get("/products/edit/{product_id}", response_class=HTMLResponse)
async def edit_product_page(request: Request, product_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    categories = db.query(Category).all()
    return templates.TemplateResponse("admin/edit_product.html", {
        "request": request, "admin": admin, "product": product, "categories": categories
    })


@router.post("/products/edit/{product_id}")
async def edit_product(
    request: Request, product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    old_price: float = Form(None),
    stock: int = Form(0),
    category_id: int = Form(None),
    is_featured: bool = Form(False),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin/products", status_code=303)

    product.name = name
    product.description = description
    product.price = price
    product.old_price = old_price if old_price else None
    product.stock = stock
    product.category_id = category_id if category_id else None
    product.is_featured = is_featured

    if image and image.filename:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        product.image = f"/static/uploads/{filename}"

    db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


@router.post("/products/delete/{product_id}")
async def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin/products", status_code=303)


# ─── ORDERS ───
@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, status: str = None, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("admin/orders.html", {
        "request": request, "admin": admin, "orders": orders, "current_status": status
    })


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_detail(request: Request, order_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/admin/orders", status_code=303)
    return templates.TemplateResponse("admin/order_detail.html", {
        "request": request, "admin": admin, "order": order
    })


@router.post("/orders/{order_id}/status")
async def update_order_status(request: Request, order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return RedirectResponse(url=f"/admin/orders/{order_id}", status_code=303)
