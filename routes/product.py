from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, SQLModel, Field, delete, update
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, JSON
from pydantic import EmailStr, validator, BaseModel, model_validator
from typing import List, Optional, Dict, Any
from routes.commonflds import CommonFields
from datetime import datetime, timedelta, date
from routes.company import Company
from routes.uom import UOM as uom

router = APIRouter(tags=["Product"])
class ProductHeader(CommonFields, table=True):
    __tablename__ = "product"
    __table_args__ = {"extend_existing": True}
    companyid: int = Field(foreign_key="company.id", nullable=False)
    productcode: str = Field(index=True, nullable=False)
    productname: str = Field(index=True, nullable=False)    
    productspec: Optional[str] = None
    selling_uom: int = Field(foreign_key="uom.id" ,  nullable=False)
    purchase_uom: int = Field(foreign_key="uom.id", nullable=False)
    selling_price: float = Field(default=0.0, nullable=False)
    cost_price: float = Field(default=0.0, nullable=False)
    hsncode: Optional[str] = None
    taxname:int = Field(foreign_key="taxheader.id", nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True  # default value

class PProduct(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default=0, nullable=False)
    productcode: str = Field(nullable=False)
    productname: str = Field(nullable=False)    
    productspec: Optional[str] = None
    selling_uom: int = Field(default=0, nullable=False)
    purchase_uom: int = Field(default=0, nullable=False)
    selling_price: float = Field(default=0.0, nullable=False)
    cost_price: float = Field(default=0.0, nullable=False)
    hsncode: Optional[str] = None
    taxname:int = Field(default=0, nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
class ProductUpdate(BaseModel):
    companyid: int = Field(default=0, nullable=False)
    modifiedby: str = Field(nullable=False)
    productcode: str = Field(nullable=False)
    productname: str = Field(nullable=False)    
    productspec: Optional[str] = None
    selling_uom: int = Field(default=0, nullable=False)
    purchase_uom: int = Field(default=0, nullable=False)
    selling_price: float = Field(default=0.0, nullable=False)
    cost_price: float = Field(default=0.0, nullable=False)
    hsncode: Optional[str] = None
    taxname:int = Field(default=0, nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True 
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }
@router.post("/productcreate", response_model=ProductHeader)
def create_product(product: PProduct, session: Session = Depends(get_session)):
    db_product = session.exec(select(ProductHeader).where(ProductHeader.productcode == product.productcode, ProductHeader.companyid == product.companyid)).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product with this code already exists in the company")
    db_product = session.exec(select(ProductHeader).where(ProductHeader.productname == product.productname, ProductHeader.companyid == product.companyid)).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product with this name already exists in the company")
    db_product = ProductHeader.from_orm(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.post("/productupdate/{productid}", response_model=ProductHeader)
def update_product(productid: int, product: ProductUpdate, session: Session = Depends(get_session)):
    db_product = session.get(ProductHeader, productid)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.get("/products/{companyid}/{product_id}", response_model=ProductHeader)
def get_product(companyid: int, product_id: int, session: Session = Depends(get_session)):
    product = session.exec(
        select(ProductHeader).where(
            ProductHeader.companyid == companyid,
            ProductHeader.id == product_id
        )
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/productdelete/{productid}")
def delete_product(productid: int, session: Session = Depends(get_session)):    
    product = session.get(ProductHeader, productid)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"detail": "Product deleted successfully"}