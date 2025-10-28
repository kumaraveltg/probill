from fastapi import APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field, delete, update,func,and_
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, JSON
from sqlalchemy.orm import aliased
from pydantic import   validator, BaseModel, model_validator
from typing import List, Optional, Dict, Any
from routes.commonflds import CommonFields
from datetime import datetime
from routes.company import Company
from routes.uom import UOM  
from routes.userauth import get_current_user
from routes.taxmaster import TaxHeader

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

class GetProduct(BaseModel):
    id: int
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default=0, nullable=False)
    companyname: str
    companyno: Optional[str] = None
    productcode: str = Field(nullable=False)
    productname: str = Field(nullable=False)    
    productspec: Optional[str] = None
    selling_uom: int = Field(default=0, nullable=False)
    purchase_uom: int = Field(default=0, nullable=False)
    selling_price: float = Field(default=0.0, nullable=False)
    cost_price: float = Field(default=0.0, nullable=False)
    hsncode: Optional[str] = None
    taxname:Optional[str] = None
    taxmasterid:int = Field(default=0, nullable=False)
    taxrate: float = Field(default=0.0, nullable=False)
    active: bool = True 
    modifiedon: datetime
    createdon: datetime
    suom: str
    puom: str
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class ProductResponse(BaseModel):
    total: int
    productlist : List[GetProduct]

 

class ProductSearch(BaseModel):
    id: int
    companyid: int
    companyname: str
    companyno: str
    productcode: str
    productname: str
    productspec: Optional[str] = None  
    selling_uom: Optional[int] = None
    purchase_uom: Optional[int] = None
    selling_price: int
    cost_price: int
    hsncode: Optional[str] = None
    taxmasterid:Optional[int] = None
    taxname: int     # changed from int → str
    taxrate: Optional[float] = 0.0
    active: bool = True
     


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

@router.get("/product/search/{companyid}",response_model=List[ProductSearch])
def product_search(
    companyid: int,
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session)
):
    # Define table aliases for readability
    p = aliased(ProductHeader)
    su = aliased(UOM)
    pu = aliased(UOM)
    c = aliased(Company)
    t = aliased(TaxHeader)

    # Base query
    query = (
        db.query(
            p.id,
            p.productcode,
            p.productname,
            p.productspec,
            p.taxrate,
            p.hsncode,
            p.selling_price,
            p.cost_price,
            p.active,
            p.companyid,
            c.companyname,
            c.companyno,
            su.id.label("sellingid"),
            pu.id.label("purchaseid"),
            t.id.label("taxmasterid"),
            su.uomcode.label("selling_uom_code"),
            pu.uomcode.label("purchase_uom_code"),
            t.taxname.label("taxname"), 
        )
        .join(c, p.companyid == c.id)
        .join(su, and_(p.selling_uom == su.id ,func.coalesce(su.active, True)))
        .outerjoin(pu, and_(p.purchase_uom == pu.id,func.coalesce(pu.active, True)))
        .outerjoin(t, p.taxname == t.id)
        .filter(
            and_(
                 c.id == companyid
            )
        )
    )

    # Dynamic filtering
    if field == "productcode":
        query = query.filter(p.productcode.ilike(f"%{value}%"))
    elif field == "productname":
        query = query.filter(p.productname.ilike(f"%{value}%"))
    elif field == "productspec":
        query = query.filter(p.productspec.ilike(f"%{value}%"))
    else:
        raise HTTPException(status_code=400, detail="Invalid search field")

    results = query.all()
    
    #  ✅ Print results for debugging
    print("🔍 Query Results:")
    for r in results:
        print(r)

    # ✅ Optional: print the generated SQL for deeper debugging
    print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))

    return [
        {
        "id": r.id,
        "productcode": r.productcode,
        "productname": r.productname,
        "productspec": r.productspec,
        "hsncode": r.hsncode,
        "selling_price": r.selling_price,
        "cost_price" : r.cost_price,
        "taxrate": r.taxrate,
        "active": r.active,
        "companyid": r.companyid,
        "companyname": r.companyname,
        "companyno": r.companyno,
        "selling_uom": r.sellingid,
        "purchase_uom": r.purchaseid,
        "taxname": r.taxmasterid,  
        "taxmasterid":r.taxmasterid,
        }
        for r in results  
         
    ]
     

@router.get("/products/{companyid}", response_model= ProductResponse)
def get_product(companyid: int, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    # Aliases
    p = aliased(ProductHeader)
    su = aliased(UOM)
    pu = aliased(UOM)
    c = aliased(Company)
    t = aliased(TaxHeader)

    # Query
    query = (
        select(
            p,
            su.uomcode.label("suom"),
            su.id.label("sellingid"),
            pu.uomcode.label("puom"),
            pu.id.label("purchaseid"),
            c.companyname,
            c.id.label("companyid"),
            c.companyno,
            t.taxname,
            t.id.label("taxmasterid"),
        )
        .join(c, p.companyid == c.id)
        .join(su, p.selling_uom == su.id)
        .join(pu, p.purchase_uom == pu.id, isouter=True)
        .join(t, p.taxname == t.id, isouter=True)
        .where(and_(su.active == True, c.id == companyid))
        .order_by(p.productname)
        .offset(skip)
        .limit(limit)
    )

    product_rows = session.exec(query).all()

    # Total count
    totalcount = session.exec(
        select(func.count(p.id)).where(p.companyid == companyid)
    ).one()

    if not product_rows:
        raise HTTPException(status_code=404, detail="Product not found")

    # Convert query rows into list of dicts (with created/modified info)
    productlist = [
    {
        "id": row[0].id,
        "productcode": row[0].productcode,
        "productname": row[0].productname,
        "productspec": row[0].productspec,
        "selling_price": row[0].selling_price,
        "cost_price": row[0].cost_price,
        "taxname": row[0].taxname,
        "taxrate": row[0].taxrate,
        "hsncode": row[0].hsncode,
        "active": row[0].active,
        "suom": row[1],        # su.uomcode
        "selling_uom": row[2], # su.id
        "puom": row[3],        # pu.uomcode
        "purchase_uom": row[4],# pu.id
        "companyname": row[5], # string
        "companyid": row[6],   # int
        "companyno": row[7],
        "taxname": row[8],     # taxname string
        "taxmasterid": row[9],         # taxmasterid int
        "createdby": row[0].createdby,
        "createdon": row[0].createdon,
        "modifiedby": row[0].modifiedby,
        "modifiedon": row[0].modifiedon,
    }
    for row in product_rows
    ]

    return {"total": totalcount, "productlist": productlist}


@router.delete("/productdelete/{productid}")
def delete_product(productid: int, session: Session = Depends(get_session)):    
    product = session.get(ProductHeader, productid)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"detail": "Product deleted successfully"}