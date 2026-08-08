from collections.abc import Generator
from typing import Any

import backend.database.models as dbModels
from backend.database.config import boot
from fastapi import Depends, FastAPI
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

engine, SessionLocal = boot()
app = FastAPI()

def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session

def model_to_dict(instance: Any) -> dict[str, Any]:
    return {
        attribute.key: getattr(instance, attribute.key)
        for attribute in inspect(instance).mapper.column_attrs
    }

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/product-suppliers")
def list_product_suppliers(
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    statement = select(dbModels.ProductSuppliers).order_by(
        dbModels.ProductSuppliers.id
    )

    product_suppliers = session.scalars(statement).all()

    return [
        model_to_dict(product_supplier)
        for product_supplier in product_suppliers
    ]
