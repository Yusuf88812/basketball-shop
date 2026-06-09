from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Product, Category

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    featured = db.query(Product).filter(Product.is_featured == True).limit(8).all()
    categories = db.query(Category).all()
    new_products = db.query(Product).order_by(Product.created_at.desc()).limit(8).all()
    return templates.TemplateResponse("store/index.html", {
        "request": request,
        "featured": featured,
        "categories": categories,
        "new_products": new_products
    })


@router.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request, category: int = None, search: str = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category_id == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    products = query.order_by(Product.created_at.desc()).all()
    categories = db.query(Category).all()
    return templates.TemplateResponse("store/catalog.html", {
        "request": request,
        "products": products,
        "categories": categories,
        "current_category": category,
        "search": search or ""
    })


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return templates.TemplateResponse("store/404.html", {"request": request}, status_code=404)
    related = db.query(Product).filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    return templates.TemplateResponse("store/product.html", {
        "request": request,
        "product": product,
        "related": related
    })


@router.get("/cart", response_class=HTMLResponse)
async def cart(request: Request):
    return templates.TemplateResponse("store/cart.html", {"request": request})


@router.get("/checkout", response_class=HTMLResponse)
async def checkout(request: Request):
    return templates.TemplateResponse("store/checkout.html", {"request": request})


@router.get("/track", response_class=HTMLResponse)
async def track(request: Request):
    return templates.TemplateResponse("store/track.html", {"request": request})
