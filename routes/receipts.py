from fastapi import  FastAPI, APIRouter, HTTPException, Depends,Query
from sqlmodel import Session, select, SQLModel, Field ,delete ,func ,and_ 
from sqlalchemy import  case,cast,Float,update
from .db import engine, get_session 
from pydantic import  validator, BaseModel ,EmailStr 
from typing import List, Optional
from routes.commonflds import CommonFields  
from datetime import datetime,date  
from routes.company import Company  
from routes.userauth import get_current_user
from routes.customer import CustomerHeader
from routes.currecny  import Currency
from routes.invoice import InvoiceHeader


router = APIRouter( tags=["Receipts"])

class ReceiptsHeader(CommonFields, table=True):
    __tablename__ = "receipts_header"
    __table_args__ = {"extend_existing": True}  
    companyid: int = Field(foreign_key="company.id", nullable=False)    
    companyno: str = Field(index=True, nullable=False)
    receiptno: str = Field(index=True, nullable=False)
    receiptdate: date = Field(nullable=False)
    receipttype: str = Field(nullable=False)
    customerid: int = Field(foreign_key="customer.id", nullable=False) 
    receiptamount: float = Field(nullable=False)
    paymentmode: str = Field(nullable=False)
    currencyid: int = Field(foreign_key="currency.id",nullable=False)
    exrate: float = Field(default=1.0, nullable=False)
    transactionno: Optional[str] = None
    transactiondate: Optional[date] = None  
    chequeno: Optional[str] = None
    cheqedate: Optional[date] = None 
    remarks: Optional[str] = None
    totalreceiptamount: float = Field(default=0, nullable=False)

class ReceiptsDetail(SQLModel, table=True):  
    __tablename__ = "receipts_detail"
    __table_args__ = {"extend_existing": True}  
    id: Optional[int] = Field(default=None, primary_key=True)
    receiptheaderid: int = Field(foreign_key="receipts_header.id", nullable=False)
    rowno: Optional[int] = Field(default=1)
    invoiceno: int = Field(foreign_key="invoice_header.id", index=True, nullable=False)
    invoicedate: date = Field(nullable=False)
    invoiceamount: float = Field(nullable=False) 
    gcurrency: int = Field(foreign_key="currency.id", nullable=False)
    gexrate: float = Field(default=1.0, nullable=False)
    greceiptamount: float = Field(nullable=False)
    commisionamount: float = Field(default=0.0)
    tdsamount: float = Field(default=0.0 )
    netreceiptamount: float = Field(nullable=False)

class ReceiptsDetailUpdate(BaseModel):
    id: Optional[int] = None
    invoiceno: int = Field( index=True, nullable=False)
    invoicedate: date = Field(nullable=False)
    invoiceamount: float = Field(nullable=False) 
    gcurrency: int = Field(nullable=False)
    gexrate: float = Field(default=1.0, nullable=False)
    greceiptamount: float = Field(nullable=False)
    commisionamount: float = Field(default=0.0)
    tdsamount: float = Field(default=0.0 )
    netreceiptamount: float = Field(nullable=False)

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }

class ReceiptsHeaderUpdate(BaseModel):
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default=0,nullable=False)    
    companyno: str = Field(nullable=False)
    receiptno: str = Field(nullable=False)
    receiptdate: date = Field(nullable=False)
    receipttype: str = Field(nullable=False)
    customerid: int = Field(default=0,nullable=False)
    receiptamount: float = Field(nullable=False)
    paymentmode: str = Field(nullable=False)
    currencyid: int = Field(nullable=False)
    exrate: float = Field(default=1.0, nullable=False)
    transactionno: Optional[str] = None
    transactiondate: Optional[date] = None  
    chequeno: Optional[str] = None
    cheqedate: Optional[date] = None 
    remarks: Optional[str] = None
    totalreceiptamount: float = Field(default=0, nullable=False)
    receipt_details: List[ReceiptsDetailUpdate] = []

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }

class ReceiptsHeaderRead(BaseModel):
    id: int
    companyid: int
    companyname: Optional[str] = None
    companyno: str
    receiptno:Optional[str] = None
    receiptdate: date
    receipttype: str
    customerid: int
    customername: Optional[str] = None
    receiptamount: float
    paymentmode: str
    currencyid: int
    currencycode: Optional[str] = None
    exrate: float
    transactionno: Optional[str] = None
    transactiondate: Optional[date] = None  
    chequeno: Optional[str] = None
    cheqedate: Optional[date] = None 
    remarks: Optional[str] = None
    totalreceiptamount: float
    createdby: str
    createdon: datetime
    modifiedby: str
    modifiedon: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }

class ReceiptsDetailCreate(BaseModel): 
    invoiceno: int = Field( index=True, nullable=False)
    invoicedate: date = Field(nullable=False)
    invoiceamount: float = Field(nullable=False) 
    gcurrency: int = Field(nullable=False)
    gexrate: float = Field(default=1.0, nullable=False)
    greceiptamount: float = Field(nullable=False)
    commisionamount: float = Field(default=0.0)
    tdsamount: float = Field(default=0.0 )
    netreceiptamount: float = Field(nullable=False)

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }

class ReceiptsHeaderCreate(BaseModel):
    createdby: str = Field(nullable=False)
    modifiedby: str = Field(nullable=False)
    companyid: int = Field(default=0,nullable=False)    
    companyno: str = Field(nullable=False)
    receiptno: Optional[str] = None
    receiptdate: date = Field(nullable=False)
    receipttype: Optional[str] = None
    customerid: int = Field(default=0,nullable=False)
    receiptamount: float = Field(nullable=False)
    paymentmode:  Optional[str] = None
    currencyid: int = Field(nullable=False)
    exrate: float = Field(default=1.0, nullable=False)
    transactionno: Optional[str] = None
    transactiondate: Optional[date] = None  
    chequeno: Optional[str] = None
    cheqedate: Optional[date] = None 
    remarks: Optional[str] = None
    totalreceiptamount: float = Field(default=0, nullable=False)
    receipt_details: List[ReceiptsDetailCreate] = []

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }

class ReceiptsHeaderResponse(BaseModel):  
    total: int
    receipts_list: List[ReceiptsHeaderRead] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }   
class Config:
    orm_mode = True
    
class ReceiptsDetailRead(BaseModel):
    id: int
    receiptheaderid: int
    invoiceno: int
    invoicedate: date
    invoiceamount: float 
    gcurrency: int
    gexrate: float
    greceiptamount: float
    commisionamount: float
    tdsamount: float
    netreceiptamount: float

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }  
class ReceiptDetailResponse(BaseModel):
    rechdr: ReceiptsHeaderRead
    recdtl: List[ReceiptsDetailRead] = []
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }


class ReceiptsSearch(BaseModel):
    id: Optional[int] = None
    companyid: Optional[int] = None
    companyno: Optional[str] = None
    receiptno: str
    receiptdate: date
    receipttype: str
    customerid: int
    customername: Optional[str] = None
    receiptamount: float
    paymentmode: str
    currencyid: Optional[int] = None
    exrate: float
    transactionno: Optional[str] = None
    transactiondate: Optional[date] = None  
    chequeno: Optional[str] = None
    cheqedate: Optional[date] = None 
    remarks: Optional[str] = None
    totalreceiptamount: float
    invoiceno: Optional[str] = None
    invoicedate: date
    invoiceamount: float 
    gcurrency: int
    gexrate: float
    greceiptamount: float
    commisionamount: float
    tdsamount: float
    netreceiptamount: float

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None,
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
    }

def get_financial_year(invoice_date: date) -> str:
    year = invoice_date.year
    if invoice_date.month < 4:  # Jan, Feb, Mar → previous FY
        start_year = year - 1
        end_year = year
    else:
        start_year = year
        end_year = year + 1
    return f"{start_year}-{str(end_year)[2:]}"

def update_invoice_receipt_amount(session: Session, invoice_id: int, commit=True):
    total_receipt = session.scalar(
    select(func.coalesce(func.sum(ReceiptsDetail.greceiptamount), 0))
    .join(ReceiptsHeader, ReceiptsHeader.id == ReceiptsDetail.receiptheaderid)
    .where(
        (ReceiptsDetail.invoiceno == invoice_id)
        & (ReceiptsHeader.cancel != 'T')
        )
    )

    session.execute(
        update(InvoiceHeader)
        .where(InvoiceHeader.id == invoice_id)
        .values(receiptamount=total_receipt)
    )

    if commit:
        session.commit()

@router.post("/addreceipts", response_model = ReceiptsHeaderCreate)
def add_receipts(payload: ReceiptsHeaderCreate, session: Session = Depends(get_session),
                  current_user: dict = Depends(get_current_user)
                  ):
    try:
        # ✅ Step 1: Determine Financial Year using Receipt date
        def get_financial_year(receiptdate: date):
            year = receiptdate.year
            if receiptdate.month < 4:  # Jan–Mar → previous FY
                start_year = year - 1
                end_year = year
            else:
                start_year = year
                end_year = year + 1
            return f"{start_year}-{str(end_year)[2:]}"  # e.g. 2025-26

        finyr = get_financial_year(payload.receiptdate)

        # ✅ Step 2: Get last invoice for same company & FY
        last_receipt = session.exec(
            select(ReceiptsHeader)
            .where(
                ReceiptsHeader.companyid == payload.companyid,
                ReceiptsHeader.receiptno.like(f"REC/{finyr}-%")
            )
            .order_by(ReceiptsHeader.id.desc())
            .limit(1)
        ).first()

        # ✅ Step 3: Determine new Receipt number
        if last_receipt and last_receipt.receiptno:
            last_part = int(last_receipt.receiptno.split("-")[-1])
            new_no = last_part + 1
        else:
            new_no = 1

        receiptno = f"REC/{finyr}-{new_no:04d}"

        db_receipt = ReceiptsHeader.from_orm(payload)
        db_receipt.receiptno = receiptno    
        session.add(db_receipt)
        session.flush()  

        for detail in payload.receipt_details:
            db_detail = ReceiptsDetail(**detail.model_dump(exclude_unset=True))
            db_detail.receiptheaderid = db_receipt.id  
            session.add(db_detail)  
        session.commit()
        session.refresh(db_receipt)

        # --- Update invoice receipt amounts ---

        unique_invoices = {d.invoiceno for d in payload.receipt_details or []}

        for invoiceno in unique_invoices:
            update_invoice_receipt_amount(session, invoiceno, commit=False)

            session.commit()

        return db_receipt

      

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/updatereceipts/{receipt_id}", response_model=ReceiptsHeaderUpdate)
def update_receipts(
    receipt_id: int,
    payload: ReceiptsHeaderUpdate,
    session: Session = Depends(get_session),
):
    # --- Fetch existing receipt header ---
    db_receipt = session.get(ReceiptsHeader, receipt_id)
    if not db_receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # --- Update header fields (excluding details) ---
    for key, value in payload.model_dump(exclude={"receipt_details"}).items():
        setattr(db_receipt, key, value)
    session.add(db_receipt)
    session.flush()  # ensure db_receipt.id exists

    # --- Fetch existing details from DB ---
    existing_details = session.exec(
        select(ReceiptsDetail).where(ReceiptsDetail.receiptheaderid == receipt_id)
    ).all()
    existing_ids = {d.id for d in existing_details}

    # --- Handle details from payload ---
    payload_ids = set()
    for detail_payload in payload.receipt_details or []:
        if detail_payload.id:  # Existing row → update
            payload_ids.add(detail_payload.id)
            db_detail = session.get(ReceiptsDetail, detail_payload.id)
            if db_detail:
                for key, value in detail_payload.model_dump(exclude_unset=True).items():
                    setattr(db_detail, key, value)
                session.add(db_detail)
            else:
                # If ID not found in DB → insert as new
                new_detail = ReceiptsDetail(
                    receiptheaderid=receipt_id,
                    **detail_payload.model_dump(exclude={"id", "receiptheaderid"})
                )
                session.add(new_detail)
        else:  # New row → insert
            new_detail = ReceiptsDetail(
                receiptheaderid=receipt_id,
                **detail_payload.model_dump(exclude={"id", "receiptheaderid"})
            )
            session.add(new_detail)

    # --- Delete removed details (existing in DB but not in payload) ---
    ids_to_delete = existing_ids - payload_ids
    if ids_to_delete:
        session.exec(
            delete(ReceiptsDetail).where(ReceiptsDetail.id.in_(ids_to_delete))
        )

    session.commit()
    session.refresh(db_receipt)

    # --- Update invoice receipt amounts ---
    unique_invoices = {d.invoiceno for d in payload.receipt_details or []}

    for invoiceno in unique_invoices:
        update_invoice_receipt_amount(session, invoiceno, commit=False)

        session.commit()

    return db_receipt


@router.get("/receiptssearch/{companyid}", response_model=List[ReceiptsSearch])
def search_receipts(
    companyid: int,
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_session),
):

    query = (
        select(ReceiptsHeader, ReceiptsDetail, InvoiceHeader)
        .join(
            ReceiptsDetail,
            ReceiptsHeader.id == ReceiptsDetail.receiptheaderid
        )
        .outerjoin(
            InvoiceHeader,
            ReceiptsDetail.invoiceno == InvoiceHeader.id
        )
        .where(ReceiptsHeader.companyid == companyid)
    )

    if field and value:
        if field == "receiptno":
            query = query.where(ReceiptsHeader.receiptno.ilike(f"%{value}%"))
        elif field == "customername":
            query = query.join(CustomerHeader, ReceiptsHeader.customerid == CustomerHeader.id).where(
                CustomerHeader.customername.ilike(f"%{value}%")
            )
        elif field == "invoiceno":
            query = query.where(InvoiceHeader.invoiceno.ilike(f"%{value}%"))
        else:
            raise HTTPException(status_code=400, detail="Invalid search field")

    results = db.execute(query).all()  # ✅ should use execute() not exec()
    response = []

    for rechdr, recdtl, invhdr in results:
        company = db.get(Company, rechdr.companyid)
        customer = db.get(CustomerHeader, rechdr.customerid)
        currency = db.get(Currency, rechdr.currencyid)

        # Convert header and detail to dict safely
        hdr_dict = rechdr.model_dump() if hasattr(rechdr, "model_dump") else rechdr.__dict__.copy()
        dtl_dict = recdtl.model_dump() if recdtl and hasattr(recdtl, "model_dump") else (recdtl.__dict__.copy() if recdtl else {})
        inv_dict = invhdr.model_dump() if invhdr and hasattr(invhdr, "model_dump") else (invhdr.__dict__.copy() if invhdr else {})

    # Merge all fields
        record = {
            **hdr_dict,
            **{
                "invoiceno": inv_dict.get("invoiceno"),
                "invoicedate": inv_dict.get("invoicedate"),
                "invoiceamount": inv_dict.get("totnetamount"),
            },
            **{
                "gcurrency": dtl_dict.get("gcurrency"),
                "gexrate": dtl_dict.get("gexrate"),
                "greceiptamount": dtl_dict.get("greceiptamount"),
                "commisionamount": dtl_dict.get("commisionamount"),
                "tdsamount": dtl_dict.get("tdsamount"),
                "netreceiptamount": dtl_dict.get("netreceiptamount"),
            },
            "companyname": company.companyname if company else None,
            "customername": customer.customername if customer else None,
        }

        response.append(ReceiptsSearch(**record))

    return response



@router.get("/receiptslist/{companyid}", response_model= ReceiptsHeaderResponse)
def get_receipts_by_company(
    companyid: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    # 1️⃣ Get total count first (without pagination)
    total_count = (
        session.query(ReceiptsHeader)
        .filter(ReceiptsHeader.companyid == companyid)
        .count()
    )

    # 2️⃣ Get paginated receipts
    db_receipts = (
        session.query(ReceiptsHeader)
        .filter(ReceiptsHeader.companyid == companyid)
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not db_receipts:
        #raise HTTPException(status_code=404, detail="No receipts found for this company")
        return ReceiptsHeaderResponse(total=0,receipts_list=[])

    # 3️⃣ Build response list
    receipt_list = []
    for db_receipt in db_receipts:
        company = session.get(Company, db_receipt.companyid)
        customer = session.get(CustomerHeader, db_receipt.customerid)
        currency = session.get(Currency, db_receipt.currencyid)

        receipt_read = ReceiptsHeaderRead.from_orm(db_receipt)
        receipt_read.companyname = company.companyname if company else None
        receipt_read.customername = customer.customername if customer else None
        receipt_read.currencycode = currency.currencycode if currency else None

        receipt_list.append(receipt_read)

    # 4️⃣ Return combined response
    return {"total": total_count, "receipts_list": receipt_list}

@router.get("/receiptdetails/{receipt_id}", response_model=ReceiptDetailResponse)
def get_receipt_details(
    receipt_id: int,
    session: Session = Depends(get_session),
    #current_user: dict = Depends(get_current_user),
):
    db_receipt = session.get(ReceiptsHeader, receipt_id)
    if not db_receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    receipt_read = ReceiptsHeaderRead.from_orm(db_receipt)

    db_details = session.exec(
        select(ReceiptsDetail).where(ReceiptsDetail.receiptheaderid == receipt_id)
    ).all()

    detail_reads = [ReceiptsDetailRead.from_orm(detail) for detail in db_details]

    return ReceiptDetailResponse(rechdr=receipt_read, recdtl=detail_reads)  

@router.delete("/deletereceipt/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    session: Session = Depends(get_session),
    #current_user: Dict = Depends(get_current_user),
):
    db_receipt = session.get(ReceiptsHeader, receipt_id)
    if not db_receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Delete associated details first
    session.exec(
        delete(ReceiptsDetail).where(ReceiptsDetail.receiptheaderid == receipt_id)
    )

    # Then delete the receipt header
    session.delete(db_receipt)
    session.commit()

    return {"detail": "Receipt deleted successfully"}   
