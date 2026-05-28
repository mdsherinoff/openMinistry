from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.config import get_db
from database.models.minister import Minister
from database.models.user import User
from api.auth import require_admin, require_moderator
from api.schemas.minister import MinisterCreate, MinisterUpdate, MinisterResponse

router = APIRouter(prefix="/api/ministers", tags=["ministers"])


@router.get("/", response_model=list[MinisterResponse])
def list_ministers(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Public endpoint — list all ministers."""
    query = db.query(Minister)
    if active_only:
        query = query.filter(Minister.is_active == 1)
    return query.order_by(Minister.name).all()


@router.get("/{minister_id}", response_model=MinisterResponse)
def get_minister(
    minister_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint — get a single minister."""
    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")
    return minister


@router.post("/", response_model=MinisterResponse)
def create_minister(
    payload: MinisterCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — create a new minister."""
    minister = Minister(**payload.model_dump())
    db.add(minister)
    db.commit()
    db.refresh(minister)
    return minister


@router.patch("/{minister_id}", response_model=MinisterResponse)
def update_minister(
    minister_id: int,
    payload: MinisterUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — update minister details."""
    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(minister, field, value)
    db.commit()
    db.refresh(minister)
    return minister


@router.delete("/{minister_id}")
def delete_minister(
    minister_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — delete a minister."""
    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")
    db.delete(minister)
    db.commit()
    return {"message": "Minister deleted"}