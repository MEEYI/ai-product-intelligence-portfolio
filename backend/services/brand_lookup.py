"""Shared validation and exact local lookup for brand-name endpoints."""

import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.brand import Brand


MAX_BRAND_NAME_LENGTH = 120


def normalize_brand_name(brand_name: str) -> str:
    """Trim surrounding whitespace while rejecting unusable query names."""
    if any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in brand_name):
        raise HTTPException(
            status_code=422,
            detail="Brand name must not contain control characters",
        )

    normalized_name = brand_name.strip()
    if not normalized_name:
        raise HTTPException(status_code=422, detail="Brand name must not be blank")
    if len(normalized_name) > MAX_BRAND_NAME_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Brand name must not exceed {MAX_BRAND_NAME_LENGTH} characters",
        )
    return normalized_name


def get_brand_by_name(db: Session, brand_name: str) -> Brand:
    """Find one local brand, treating names as literal, case-insensitive text."""
    normalized_name = normalize_brand_name(brand_name)
    lookup_name = normalized_name.casefold()

    # Python casefold/strip also handles Unicode names and legacy surrounding
    # whitespace that SQLite's built-in lower/trim do not fully support.
    matches = [
        brand
        for brand in db.query(Brand).order_by(Brand.brand_code).all()
        if brand.brand_name.strip().casefold() == lookup_name
    ]

    if not matches:
        raise HTTPException(status_code=404, detail="Brand not found")

    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Multiple brands match this name; use a brand ID",
                "reason": "brand_name_ambiguous",
                "brand_name": normalized_name,
                "matches": [
                    {
                        "id": brand.id,
                        "brand_code": brand.brand_code,
                        "brand_name": brand.brand_name,
                    }
                    for brand in matches
                ],
            },
        )

    return matches[0]
