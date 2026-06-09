from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import engine, Base, SessionLocal
from models import Admin, Category, Product, Order, OrderItem
from auth import create_default_admin
from routers import store, admin, api
import os

app = FastAPI(title="🏀 Basketball Shop")

os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(store.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_default_admin(db)
    finally:
        db.close()
    print("🏀 Basketball Shop is running!")
    print("🌐 Store: http://localhost:8000")
    print("🔐 Admin: http://localhost:8000/admin")
    print("👤 Login: admin / admin123")
