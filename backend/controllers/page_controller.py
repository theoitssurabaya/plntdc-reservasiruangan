from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from config.database import get_db
from models.setting import Page

router = APIRouter(tags=["Pages"])


@router.get("/api/page/{slug}")
def get_page_api(slug: str, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Halaman tidak ditemukan")
    return {
        "status": True,
        "data": {
            "title": page.page_title,
            "title_en": page.page_title_en,
            "body": page.page_body,
            "body_en": page.page_body_en
        }
    }

