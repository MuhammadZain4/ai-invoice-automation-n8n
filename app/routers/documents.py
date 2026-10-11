import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
import pdfplumber
router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Only PDF, PNG, JPG allowed")

    # MAX_SIZE + 1 bytes tak hi read karo, bari file se RAM na bhare
    content = await file.read(MAX_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"
    save_path.write_bytes(content)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "status": "uploaded",
    }

@router.get("/{file_id}/text")
def get_document_text(file_id: str):
    # 1. file_id validate karo (path traversal se bachne ke liye)
    try:
        file_id = str(uuid.UUID(file_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_id")

    # 2. file dhoondo (extension pata nahi, isliye glob)
    matches = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")
    path = matches[0]

    # 3. abhi sirf PDF
    if path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Text extraction abhi sirf PDF ke liye hai")

    # 4. text nikalo
    try:
        with pdfplumber.open(path) as pdf:
            pages = [(page.extract_text() or "") for page in pdf.pages]
    except Exception:
        raise HTTPException(status_code=422, detail="PDF read nahi ho saki")

    text = "\n".join(pages).strip()

    return {
        "file_id": file_id,
        "text": text,
        "char_count": len(text),
        "pages": len(pages),
        "needs_ocr": len(text) == 0,
    }