from fastapi import APIRouter, HTTPException, UploadFile, File, Form 
from pathlib import Path
import shutil
from fastapi.responses import FileResponse
import mimetypes

router = APIRouter(tags=["Upload"])

@router.post("/upload")
async def upload_invoice_attachment(
    companyno: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        contents = await file.read()
        if len(contents) > 3 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 3MB")

        file.file.seek(0)

        BASE_DIR = Path(__file__).resolve().parent.parent
        UPLOAD_DIR = BASE_DIR / "uploads" / companyno / "invoice"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        filename = file.filename
        file_path = UPLOAD_DIR / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "attachedfile": f"/uploads/{companyno}/invoice/{filename}",
            "attachedfilename": filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upload/{companyno}/{filename}")
async def get_uploaded_file(companyno: str, filename: str):
    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / "uploads" / companyno / "invoice" / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(str(file_path))
    media_type = media_type or "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
         headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )