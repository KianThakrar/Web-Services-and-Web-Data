"""Constructor read endpoints — list with filtering and individual lookup."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.constructor import Constructor
from app.schemas.constructor import ConstructorResponse

router = APIRouter(prefix="/api/v1/constructors", tags=["Constructors"])


@router.get("", response_model=list[ConstructorResponse])
def list_constructors(nationality: str | None = None, db: Session = Depends(get_db)):
    """List all constructors, optionally filtered by nationality."""
    query = db.query(Constructor)
    if nationality:
        query = query.filter(Constructor.nationality == nationality)
    return query.order_by(Constructor.name).all()


@router.get("/{constructor_id}", response_model=ConstructorResponse)
def get_constructor(constructor_id: int, db: Session = Depends(get_db)):
    """Retrieve a single constructor by ID."""
    constructor = db.query(Constructor).filter(Constructor.id == constructor_id).first()
    if not constructor:
        raise HTTPException(status_code=404, detail="Constructor not found")
    return constructor
