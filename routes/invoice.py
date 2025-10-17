from fastapi import  FastAPI, APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete ,func ,Table,MetaData,and_ 
from .db import engine, get_session
#from sqlalchemy.orm import aliassed
from pydantic import  validator, BaseModel ,EmailStr 
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date ,timedelta 
from routes.company import Company  
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
    totnetamount:float
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
    gcgstamount:Optional[float] = None
    gsgstamount:Optional[float] = None
    gigstamount:Optional[float] = None
    taxamount:Optional[float] = None
    netamount:Optional[float] = None 
    afterdiscountamount:Optional[float] = None

  #pydantic model For New Invoices 

class CustomerView(SQLModel,table=True):
    __tablename__ = "vw_customer"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    companyid : int
    customername: str
    contactperson: str
    address1: str
    address2: str    
    cityname: str
    statename: str
    countryname: str
    pincode: str
    shipping_address1: str
    shipping_address2: str
    shipping_cityname: str
    shipping_statename:str
    shipping_countryname: str
    shipping_pincode: str
    gstin: str
    currencycode: str
    placeof_supply: str
    active: bool
    customer_email:str
    customer_mobile:str

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
    invoicedate: date
    customerid: int
    customername: str
    currencyid: int
    currencycode: str
    exrate: float
    supplytype: str
    grossamount: float
    taxamt: float
    totnetamount: float
    cancel: str
    referenceno:str
    referencedate: date
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class InvoiceDetailView(SQLModel, table=True):
    __tablename__ = "vw_invoicedetail"

    id: Optional[int] = Field(default=None, primary_key=True)
    rowno: int
    itemid: int
    productname: Optional[str] = None
    productcode: Optional[str] = None
    uomid: int
    uomcode: Optional[str] = None
    invoiceqty: float
    invoicerate: float
    invoiceamount: float
    taxheaderid: Optional[int] = None
    taxname: Optional[str] = None    # ✅ make it optional
    taxrate: Optional[float] = None
    taxamount: Optional[float] = None
    sgstper: Optional[float] = None
    cgstper: Optional[float] = None
    igstper: Optional[float] = None
    gsgstamount: Optional[float] = None
    gcgstamount: Optional[float] = None
    gigstamount: Optional[float] = None
    netamount:Optional[float] = None
    invoice_headerid: int
    afterdiscountamount:Optional[float] = None
    
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
  gcgstamount:Optional[float] = Field(default=0.00 )
  gsgstamount:Optional[float] = Field(default=0.00 )
  gigstamount:Optional[float] = Field(default=0.00 )
  taxamount:Optional[float] = Field(default=0.00 )
  netamount:Optional[float] = Field(default=0.00 )
  afterdiscountamount: Optional[float] = Field(default=0.00)
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
    totnetamount:Optional[float] = Field(default=0.00 )
    invdetails: List[PostInvoiceDetails] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class UpdateInvoiceDetails(BaseModel):
  id: Optional[int] = None
  invoice_headerid: Optional[int] = None
  rowno: int = Field(default=1 )
  itemid: Optional[int] = None  
  uomid: Optional[int] = None 
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
  gcgstamount:Optional[float] = Field(default=0.00 )
  gsgstamount:Optional[float] = Field(default=0.00 )
  gigstamount:Optional[float] = Field(default=0.00 )
  taxamount:Optional[float] = Field(default=0.00 )
  netamount:Optional[float] = Field(default=0.00 )
  afterdiscountamount: Optional[float] = Field(default=0.00)
class Config:
    orm_mode = True  # <-- important

class UpdateInvoiceHeader(BaseModel):
    modifiedby: str
    companyid: int  
    companyno: str   
    invoiceno: str
    invoicedate:date
    customerid:int  
    referenceno: Optional[str] = None
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
    totnetamount:float
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
    itemid: Optional[int] = None
    productname: Optional[str] = None
    productcode: Optional[str] = None
    uomid: Optional[int] = None
    uomcode: Optional[str] = None
    invoiceqty: Optional[float] = 0
    invoicerate: Optional[float] = 0
    invoiceamount: Optional[float] = 0
    taxid: Optional[int] = None
    taxname: Optional[str] = None
    taxrate: Optional[float] = 0
    taxamount: Optional[float] = 0
    sgstper: Optional[float] = 0
    cgstper: Optional[float] = 0
    igstper: Optional[float] = 0
    sgstamount: Optional[float] = 0
    cgstamount: Optional[float] = 0
    igstamount: Optional[float] = 0
    afterdiscountamount:Optional[float] = 0

class InvoicePDFHeader(BaseModel):
    companyname: str
    adress: str
    phone: str | None
    emailid: str | None
    gstno: str | None

    customername: str
    contactperson: str | None
    currencycode: str | None
    customer_email: str | None
    customer_mobile: str | None

    address1: str | None
    address2: str | None
    cityname: str | None
    statename: str | None
    countryname: str | None
    pincode: str | None

    shipping_address1: str | None
    shipping_address2: str | None
    shipping_cityname: str | None
    shipping_statename: str | None
    shipping_countryname: str | None
    shipping_pincode: str | None

    gstin: str | None
    placeof_supply: str | None
    active: bool | None
 
    invoicedate: date
    referenceno: str | None
    referencedate: date | None
    remarks: str | None
    invoiceno: str| None
    


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
            totnetamount=payload.totnetamount,
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
                gcgstamount=invdetails.gcgstamount,
                gsgstamount=invdetails.gsgstamount,
                gigstamount=invdetails.gigstamount,
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
                        **invdetails.model_dump(exclude={"id","invoice_headerid"})
                    )
                    session.add(new_detail)
            else:  # new detail → insert
                new_detail = InvoiceDetails(
                    invoice_headerid=invoiceid,
                    **invdetails.model_dump(exclude={"id","invoice_headerid"})
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
            d.productname,
            d.productcode,
            d.itemid,
            d.uomid,
            d.uomcode,
            d.invoiceqty,
            d.invoicerate,
            d.invoiceamount,
            d.taxheaderid,
            d.taxname,
            d.taxrate,
            d.taxamount,
            d.sgstper,
            d.cgstper,
            d.igstper,
            d.gsgstamount,
            d.gcgstamount,
            d.gigstamount,
            d.afterdiscountamount 
        )
        .join(comp, c.companyid == comp.id, isouter=True)
        .join(d, c.id == d.invoice_headerid, isouter=True)
        .filter(comp.id == companyid)
    )

    # Dynamic filter
    field_map = {
        "customername": c.customername,
        "invoiceno": c.invoiceno,
        "invoicedate": c.invoicedate,
        "productname": d.productname,
    }

    if field not in field_map:
        raise HTTPException(status_code=400, detail="Invalid search field")

    query = query.filter(field_map[field].ilike(f"%{value}%"))

    results = query.all()

    response_data = []
    for row in results:
        # Unpack query result tuple
        r, companyname, customername, invoiceno, invoicedate, productname, productcode, \
        itemid, uomid, uomcode, invoiceqty, invoicerate, invoiceamount, taxid, taxname, \
        taxrate, taxamount, sgstper, cgstper, igstper, sgstamount, cgstamount, igstamount = row

        record = r.model_dump() if hasattr(r, "model_dump") else r.__dict__.copy()
        
        # Fill header + line item fields
        record.update({
            "companyname": companyname,
            "customername": customername,
            "invoiceno": invoiceno,
            "invoicedate": invoicedate,
            "productname": productname,
            "productcode": productcode,
            "itemid": itemid,
            "uomid": uomid,
            "uomcode": uomcode,
            "invoiceqty": invoiceqty or 0,
            "invoicerate": invoicerate or 0,
            "invoiceamount": invoiceamount or 0,
            "taxid": taxid,
            "taxname": taxname,
            "taxrate": taxrate or 0,
            "taxamount": taxamount or 0,
            "sgstper": sgstper or 0,
            "cgstper": cgstper or 0,
            "igstper": igstper or 0,
            "sgstamount": sgstamount or 0,
            "cgstamount": cgstamount or 0,
            "igstamount": igstamount or 0,
            "afterdiscountamount":afterdiscountamount or 0
        })

        response_data.append(InvoiceSearch(**record))

    return response_data



@router.get("/getinvoice/{companyid}", response_model=InvoiceResponse)
def read_invoice(
    companyid: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
     current_user: dict = Depends(get_current_user)
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

    statement = statement = (
    select(InvoiceDetails)
    .where(InvoiceDetails.invoice_headerid == invoiceid)
    .order_by(InvoiceDetails.rowno)
            )
    results = session.exec(statement) 
    inv_details = results.all()

    return InvoiceDetailResponse(invhdr=inv_header, invdtl=inv_details)

  

@router.get("/getinvpdfhdr/{invoiceid}", response_model=List[InvoicePDFHeader])
def get_invpdfhdr(invoiceid: int, session: Session = Depends(get_session)):

    # Tables
    comp = Company
    cust = CustomerView
    inv = InvoiceHeader

    # Build query
    statement = (
        select(
            comp.companyname,
            comp.adress,
            comp.phone,
            comp.emailid,
            comp.gstno,
            cust.customername,
            cust.contactperson,
            cust.currencycode,
            cust.customer_email,
            cust.customer_mobile,
            cust.address1,
            cust.address2,
            cust.cityname,
            cust.statename,
            cust.countryname,
            cust.pincode,
            cust.shipping_address1,
            cust.shipping_address2,
            cust.shipping_cityname,
            cust.shipping_statename,
            cust.shipping_countryname,
            cust.shipping_pincode,
            cust.gstin,
            cust.placeof_supply,
            cust.active, 
            inv.invoicedate,
            inv.referenceno,
            inv.referencedate,
            inv.remarks,
            inv.invoiceno,
        )
        .select_from(comp)
        .join(cust, comp.id == cust.companyid)
        .join(inv, cust.id == inv.customerid)
        .where(inv.id == invoiceid)
    )

    results = session.exec(statement).all()

    if not results:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Map to InvoicePDFHeader
    response = []
    for r in results:
    # r is a tuple in the order of your select
     response.append(
        InvoicePDFHeader(
            companyname=str(r[0]),
            adress=str(r[1]),
            phone=r[2] if r[2] else None,
            emailid=r[3] if r[3] else None,
            gstno=r[4] if r[4] else None,
            customername=str(r[5]),
            contactperson=r[6] if r[6] else None,
            currencycode=r[7] if r[7] else None,
            customer_email=r[8] if r[8] else None,
            customer_mobile=r[9] if r[9] else None,
            address1=r[10] if r[10] else None,
            address2=r[11] if r[11] else None,
            cityname=r[12] if r[12] else None,
            statename=r[13] if r[13] else None,
            countryname=r[14] if r[14] else None,
            pincode=r[15] if r[15] else None,
            shipping_address1=r[16] if r[16] else None,
            shipping_address2=r[17] if r[17] else None,
            shipping_cityname=r[18] if r[18] else None,
            shipping_statename=r[19] if r[19] else None,
            shipping_countryname=r[20] if r[20] else None,
            shipping_pincode=r[21] if r[21] else None,
            gstin=r[22] if r[22] else None,
            placeof_supply=r[23] if r[23] else None,
            active=bool(r[24]) if r[24] is not None else None,
            invoicedate=r[25] if isinstance(r[25], date) else None,
            referenceno=r[26] if r[26] else None,
            referencedate=r[27] if isinstance(r[27], date) else None,
            remarks=r[28] if r[28] else None,
            invoiceno=r[29]
        )
    )

    return response


    
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

