from fastapi import  FastAPI, APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete ,func ,Table,MetaData,and_ 
from .db import engine, get_session
#from sqlalchemy.orm import aliassed
from pydantic import  validator, BaseModel ,EmailStr 
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date  
from routes.company import Company  
from routes.city import City 
from routes.userauth import get_current_user

router = APIRouter( tags=["Invoice"])

class InvoiceHeader(CommonFields, table=True):
    __tablename__ = "invoice_header"
    __table_args__ = {"extend_existing": True} 
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: str  
    invoiceno: str
    invoicedate:date
    customerid:int = Field(foreign_key="customer.id",nullable=False)
    referenceno:str
    referencedate:date
    currencyid: int = Field(foreign_key="currency.id",nullable=False)    
    exrate: float
    supplytype:str
    remarks: str
    grossamount:float
    sgstamount:float
    cgstamount:float
    igstamount:float
    discountamount:float
    add_othercharges:float
    ded_othercharges:float
    roundedoff:float
    netamount:float
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class InvoiceDetails(SQLModel,table=True):
    __tablename__ = "invoice_details"
    __table_args__ = {"extend_existing": True} 
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_headerid: int = Field(foreign_key="invoice_header.id", nullable=False)
    rowno: int = Field(default=1 )
    itemid: int = Field(foreign_key="product.id",nullable=False)
    uomid: int = Field(foreign_key="uom.id",nullable=False)
    invoiceqty: float
    invoicerate: float
    invoiceamount:float
    discounttype:Optional[str]= None
    discount_amt_per: Optional[float] = None
    taxheaderid: int = Field(foreign_key="taxheader.id",nullable=True)
    taxrate:float
    cgstper:Optional[float] = None
    sgstper:Optional[float] = None
    igstper:Optional[float] = None
    cgstamount:Optional[float] = None
    sgstamount:Optional[float] = None
    igstamount:Optional[float] = None
    taxamount:Optional[float] = None
    netamount:Optional[float] = None

  #pydantic model For New Invoices 

class InvoiceView(SQLModel,table=True):
    __tablename__ = "vw_invoice"
    id: int | None = Field(default=None, primary_key=True)
    createdby:str
    modifiedby: str
    createdon: datetime
    modifiedon: datetime
    companyid: int  
    companyno: str
    companyid: int
    companyname: str
    invoiceno: str
    invoicedate: date
    customerid: int
    customername: str
    currencyid: int
    currencycode: str
    exrate: float
    supplytype: str
    grossamount: float
    taxamt: float
    netamount: float
    cancel: str
    referenceno:str
    referencedate: date
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class InvoiceDetailView(SQLModel,table=True):
    __tablename__ = "vw_invoicedetail"
    id: int | None = Field(default=None, primary_key=True)
    rowno: int
    itemid: int
    productname: str
    productcode: str
    uomid:int
    uomcode: str
    invoiceqty: float
    invoicerate: float
    invoiceamount:float
    taxheaderid:int
    taxname: str
    taxrate: float
    taxamount: float   
    sgstper: float
    cgstper: float
    igstper: float
    sgstamount: float
    cgstamount: float
    sgstamount: float 

class PostInvoiceDetails(BaseModel):
  id: Optional[int] = None
  invoice_headerid: Optional[int]= None  
  rowno: int = Field(default=1 )
  itemid: int = Field(foreign_key="product.id",nullable=False)
  uomid: int = Field(foreign_key="uom.id",nullable=False)
  invoiceqty: float = Field(default=0.000 )
  invoicerate: float= Field(default=0.00 )
  invoiceamount:float = Field(default=0.00 )
  discounttype:Optional[str] = None
  discount_amt_per: Optional[float] = Field(default=0.00 )
  taxheaderid: int = Field(foreign_key="taxheader.id",nullable=True)
  taxrate:float
  cgstper:Optional[float] = Field(default=0.00 )
  sgstper:Optional[float] = Field(default=0.00 )
  igstper:Optional[float] = Field(default=0.00 )
  cgstamount:Optional[float] = Field(default=0.00 )
  sgstamount:Optional[float] = Field(default=0.00 )
  igstamount:Optional[float] = Field(default=0.00 )
  taxamount:Optional[float] = Field(default=0.00 )
  netamount:Optional[float] = Field(default=0.00 )
class Config:
    orm_mode = True  # <-- important

class PostInvoiceHeader(BaseModel):
    createdby: str
    modifiedby: str
    companyid: int = Field(foreign_key="company.id", nullable=False)
    companyno: str   
    invoiceno: str
    invoicedate:date
    customerid:int = Field(foreign_key="customer.id",nullable=False)
    referenceno:Optional[str] = None
    referencedate:Optional[date] = None
    currencyid: int = Field(foreign_key="currency.id",nullable=False)    
    exrate: float = Field(default=1.00)
    supplytype:str
    remarks: Optional[str]= None
    grossamount:Optional[float] = Field(default=0.00 )
    sgstamount:Optional[float] = Field(default=0.00 )
    cgstamount:Optional[float] = Field(default=0.00 )
    igstamount:Optional[float] = Field(default=0.00 )
    discountamount:Optional[float] = Field(default=0.00 )
    add_othercharges:Optional[float] = Field(default=0.00 )
    ded_othercharges:Optional[float] = Field(default=0.00 )
    roundedoff:Optional[float] = Field(default=0.00 )
    netamount:Optional[float] = Field(default=0.00 )
    invdetails: List[PostInvoiceDetails] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class UpdateInvoiceDetails(BaseModel):
  id: int
  invoice_headerid: int  
  rowno: int = Field(default=1 )
  itemid: int  
  uomid: int  
  invoiceqty: float = Field(default=0.000 )
  invoicerate: float= Field(default=0.00 )
  invoiceamount:float = Field(default=0.00 )
  discounttype:Optional[str]= Field(default=0.00 )
  discount_amt_per: Optional[float] = Field(default=0.00 )
  taxheaderid: int  
  taxrate:float
  cgstper:Optional[float] = Field(default=0.00 )
  sgstper:Optional[float] = Field(default=0.00 )
  igstper:Optional[float] = Field(default=0.00 )
  cgstamount:Optional[float] = Field(default=0.00 )
  sgstamount:Optional[float] = Field(default=0.00 )
  igstamount:Optional[float] = Field(default=0.00 )
  taxamount:Optional[float] = Field(default=0.00 )
  netamount:Optional[float] = Field(default=0.00 )
class Config:
    orm_mode = True  # <-- important

class UpdateInvoiceHeader(BaseModel):
    modifiedby: str
    companyid: int  
    companyno: str   
    invoiceno: str
    invoicedate:date
    customerid:int  
    referenceno:str
    referencedate:date
    currencyid: int      
    exrate: float = Field(default=1.00)
    supplytype:str
    remarks: str
    grossamount:float
    sgstamount:float
    cgstamount:float
    igstamount:float
    discountamount:float
    add_othercharges:float
    ded_othercharges:float
    roundedoff:float
    netamount:float
    invdetails: List[UpdateInvoiceDetails] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class InvoiceResponse(BaseModel):
    total:int
    invoice_list: List[InvoiceView]

class InvoiceDetailResponse(BaseModel):
    invhdr: InvoiceView
    invdtl: List[InvoiceDetailView]
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class InvoiceSearch(BaseModel):
    id: int  
    createdby:str
    modifiedby: str
    createdon: datetime
    modifiedon: datetime
    companyid: int  
    companyno: str 
    invoiceno: str
    invoicedate: date
    customerid: int
    customername: str
    currencyid : int
    currencycode: str
    exrate: float
    supplytype: str
    grossamount: float
    netamount: float
    taxamt : float
    itemid: int
    productname: str
    productcode: str
    uomid: int
    uomcode: str
    invoiceqty: float
    invoicerate: float
    invoiceamount: float
    taxid: int
    taxname: str
    taxrate: float
    taxamount: float
    sgstper: float
    cgstper: float
    igstper: float
    sgstamount: float
    cgstamount: float
    igstamount: float


def get_financial_year(invoice_date: date) -> str:
    year = invoice_date.year
    if invoice_date.month < 4:  # Jan, Feb, Mar → previous FY
        start_year = year - 1
        end_year = year
    else:
        start_year = year
        end_year = year + 1
    return f"{start_year}-{str(end_year)[2:]}"


@router.post("/addinvoice", response_model=PostInvoiceHeader)
def create_invoice(payload: PostInvoiceHeader, session: Session = Depends(get_session)):
    try:
        # ✅ Step 1: Determine Financial Year using invoice date
        def get_financial_year(invoice_date: date):
            year = invoice_date.year
            if invoice_date.month < 4:  # Jan–Mar → previous FY
                start_year = year - 1
                end_year = year
            else:
                start_year = year
                end_year = year + 1
            return f"{start_year}-{str(end_year)[2:]}"  # e.g. 2025-26

        finyr = get_financial_year(payload.invoicedate)

        # ✅ Step 2: Get last invoice for same company & FY
        last_invoice = session.exec(
            select(InvoiceHeader)
            .where(
                InvoiceHeader.companyid == payload.companyid,
                InvoiceHeader.invoiceno.like(f"INV/{finyr}-%")
            )
            .order_by(InvoiceHeader.id.desc())
            .limit(1)
        ).first()

        # ✅ Step 3: Determine new invoice number
        if last_invoice and last_invoice.invoiceno:
            last_part = int(last_invoice.invoiceno.split("-")[-1])
            new_no = last_part + 1
        else:
            new_no = 1

        invoiceno = f"INV/{finyr}-{new_no:04d}"

        # ✅ Step 4: Create Invoice Header
        db_invoice = InvoiceHeader(
            companyid=payload.companyid,
            companyno=payload.companyno, 
            invoicedate=payload.invoicedate,
             invoiceno=invoiceno,  # <-- Auto-generated number
            customerid=payload.customerid,
            referenceno=payload.referenceno,
            referencedate=payload.referencedate,
            currencyid=payload.currencyid,
            exrate=payload.exrate,
            supplytype=payload.supplytype,
            remarks=payload.remarks,
            grossamount=payload.grossamount,
            sgstamount=payload.sgstamount,
            cgstamount=payload.cgstamount,
            igstamount=payload.igstamount,
            discountamount=payload.discountamount,
            add_othercharges=payload.add_othercharges,
            ded_othercharges=payload.ded_othercharges,
            roundedoff=payload.roundedoff,
            netamount=payload.netamount,
            createdby=payload.createdby,
            modifiedby=payload.modifiedby
        )

        session.add(db_invoice)
        session.flush()  # ensures db_invoice.id is available

        # ✅ Step 5: Add invoice details
        for invdetails in payload.invdetails:
            db_invdetails = InvoiceDetails(
                invoice_headerid=db_invoice.id,
                rowno=invdetails.rowno,
                itemid=invdetails.itemid,
                uomid=invdetails.uomid,
                invoiceqty=invdetails.invoiceqty,
                invoicerate=invdetails.invoicerate,
                invoiceamount=invdetails.invoiceamount,
                discounttype=invdetails.discounttype,
                discount_amt_per=invdetails.discount_amt_per,
                taxheaderid=invdetails.taxheaderid,
                taxrate=invdetails.taxrate,
                cgstper=invdetails.cgstper,
                sgstper=invdetails.sgstper,
                igstper=invdetails.igstper,
                cgstamount=invdetails.cgstamount,
                sgstamount=invdetails.sgstamount,
                igstamount=invdetails.igstamount,
                taxamount=invdetails.taxamount,
                netamount=invdetails.netamount,
            )
            session.add(db_invdetails)

        # ✅ Step 6: Commit everything
        session.commit()
        session.refresh(db_invoice)
        return db_invoice

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving Invoice: {str(e)}")

@router.post("/updateinvoice/{invoiceid}", response_model=UpdateInvoiceHeader)
def update_invoice(
    invoiceid: int,
    upd: UpdateInvoiceHeader,
    session: Session = Depends(get_session),
    # cu: dict = Depends(get_current_user),
):
    db_invoice = session.get(InvoiceHeader, invoiceid)
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # --- Update header fields ---
    for key, value in upd.model_dump(exclude={"invdetails"}).items():
        setattr(db_invoice, key, value)

    session.add(db_invoice)
    session.flush()  # make sure it's updated before adding details

    # --- Update details ---
    if upd.invdetails:
        for invdetails in upd.invdetails:
            if invdetails.id:  # existing detail → update
                db_detail = session.get(InvoiceDetails, invdetails.id)
                if db_detail:
                    for key, value in invdetails.model_dump(exclude_unset=True).items():
                        setattr(db_detail, key, value)
                    session.add(db_detail)
                else:
                    # detail.id given but not found → create new
                    new_detail = InvoiceDetails(
                        invoice_headerid=invoiceid,
                        **invdetails.model_dump(exclude={"id"})
                    )
                    session.add(new_detail)
            else:  # new detail → insert
                new_detail = InvoiceDetails(
                    invoice_headerid=invoiceid,
                    **invdetails.model_dump(exclude={"id"})
                )
                session.add(new_detail)

    session.commit()
    session.refresh(db_invoice)
    return db_invoice


@router.get("/invoice/search/{companyid}", response_model=List[InvoiceSearch])
def invoice_search(
    companyid: int,
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session),
):
    c = InvoiceView
    d = InvoiceDetailView
    comp = Company

    # Base query with joins
    query = (
        db.query(
            c,
            comp.companyname.label("companyname"),
            c.customername,
            c.invoiceno,
            c.invoicedate,
            d.productname
        )
        .join(comp, c.companyid == comp.id, isouter=True)
        .join(d, c.id == d.invoice_headerid, isouter=True)
        .filter(comp.id == companyid)
    )

    # ✅ Dynamic filter based on field
    field_map = {
        "customername": c.customername,
        "invoiceno": c.invoiceno,
        "invoicedate": c.invoicedate,
        "productname": d.productname,
    }

    if field not in field_map:
        raise HTTPException(status_code=400, detail="Invalid search field")

    query = query.filter(field_map[field].ilike(f"%{value}%"))

    # ✅ Execute query
    results = query.all()

    # ✅ Convert to list of InvoiceSearch models
    response_data = []
    for r, companyname, customername, invoiceno, invoicedate, productname in results:
        record = r.model_dump() if hasattr(r, "model_dump") else r.__dict__.copy()
        record["companyname"] = companyname
        record["customername"] = customername
        record["invoiceno"] = invoiceno
        record["invoicedate"] = invoicedate
        record["productname"] = productname
        response_data.append(InvoiceSearch(**record))

    return response_data



@router.get("/getinvoice/{companyid}", response_model=InvoiceResponse)
def read_invoice(
    companyid: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    # current_user: dict = Depends(get_current_user)
):
    c = InvoiceView

    # Fetch paginated customers
    invoice_header = session.exec(
        select(c)
        .where( c.companyid == companyid)
        .order_by(c.invoiceno)
        .offset(skip)
        .limit(limit)
    ).all()

    if not invoice_header:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Total count
    totalcount = session.exec(
        select(func.count(c.id)).where(c.companyid == companyid)
    ).first() or 0

    # Response
    return InvoiceResponse(
        total=totalcount,
        invoice_list=invoice_header
    )

@router.get("/getinvoicedtl/{invoiceid}",response_model=InvoiceDetailResponse)
def get_invdetails(invoiceid: int, session: Session = Depends(get_session),
                  #current_user: dict = Depends(get_current_user)
                 ):
    inv_header = session.get(InvoiceView, invoiceid)
    if not inv_header:
        raise HTTPException(status_code=404, detail="Invoice header not found")

    statement = select(InvoiceDetails).where(InvoiceDetails.invoice_headerid == invoiceid) 
    results = session.exec(statement)
    inv_details = results.all() 

    return InvoiceDetailResponse(custhdr=inv_header, custdtl=inv_details)

@router.delete("/invoicedelete/{invoiceid}", response_model=dict)
def delete_invoice(invoiceid: int, session: Session = Depends(get_session)):    
    db_tax = session.get(InvoiceHeader, invoiceid)
    if not db_tax:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Delete associated tax details first
    session.exec(delete(InvoiceDetails).where(InvoiceDetails.invoice_headerid == invoiceid))
    session.commit()

    # Delete the tax header
    session.delete(db_tax)
    session.commit()

    return {"detail": "Invoice deleted successfully"}
