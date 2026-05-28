from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.config import get_db
from database.models.source import Source
from database.models.user import User
from api.auth import require_admin, require_moderator
from api.schemas.source import SourceCreate, SourceUpdate, SourceResponse

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/", response_model=list[SourceResponse])
def list_sources(
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """List all sources — moderator and admin only."""
    return db.query(Source).order_by(Source.name).all()


@router.post("/", response_model=SourceResponse)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Create a new source — admin only."""
    existing = db.query(Source).filter(Source.website == payload.website).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source with this website already exists",
        )
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Update source settings — admin only."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a source — admin only."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"message": "Source deleted"}