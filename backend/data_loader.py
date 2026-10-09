"""
data_loader.py — Loads MoSPI datasets from JSON files and provides query helpers.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve data directory relative to project root
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load(filename: str) -> Dict[str, Any]:
    with open(_DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Cached dataset loading
# ─────────────────────────────────────────────────────────────────────────────
_cache: Dict[str, Any] = {}


def _get(key: str, filename: str) -> Dict[str, Any]:
    if key not in _cache:
        _cache[key] = _load(filename)
    return _cache[key]


def get_plfs_raw() -> Dict:
    return _get("plfs", "plfs.json")


def get_cpi_raw() -> Dict:
    return _get("cpi", "cpi.json")


def get_nas_raw() -> Dict:
    return _get("nas", "nas.json")


def get_iip_raw() -> Dict:
    return _get("iip", "iip.json")


def get_asi_raw() -> Dict:
    return _get("asi", "asi.json")


def get_literacy_raw() -> Dict:
    return _get("literacy", "literacy.json")


def get_poverty_raw() -> Dict:
    return _get("poverty", "poverty.json")


def get_metadata() -> Dict:
    return _get("metadata", "metadata.json")


# ─────────────────────────────────────────────────────────────────────────────
# PLFS queries
# ─────────────────────────────────────────────────────────────────────────────
def query_plfs(
    year: Optional[str] = None,
    area: Optional[str] = None,
    gender: Optional[str] = None,
) -> List[Dict]:
    """Filter PLFS records by year, area (Rural/Urban), gender (Male/Female/Persons)."""
    records = get_plfs_raw()["data"]
    result = []
    for r in records:
        if year and not _fuzzy_year_match(r.get("year", ""), year):
            continue
        if area and r.get("area", "").lower() != area.lower():
            continue
        if gender and r.get("gender", "").lower() != gender.lower():
            continue
        result.append(r)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# CPI queries
# ─────────────────────────────────────────────────────────────────────────────
def query_cpi(
    year: Optional[int] = None,
    month: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict]:
    """Filter CPI records. category: General | Food | Fuel"""
    records = get_cpi_raw()["data"]
    result = []
    for r in records:
        if year and r.get("year") != int(year):
            continue
        if month and r.get("month", "").lower() != month.lower():
            continue
        result.append(r)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# NAS queries
# ─────────────────────────────────────────────────────────────────────────────
def query_nas(year: Optional[str] = None) -> List[Dict]:
    """Filter NAS records by year."""
    records = get_nas_raw()["data"]
    if not year:
        return records
    return [r for r in records if _fuzzy_year_match(r.get("year", ""), year)]


# ─────────────────────────────────────────────────────────────────────────────
# IIP queries
# ─────────────────────────────────────────────────────────────────────────────
def query_iip(
    year: Optional[int] = None,
    month: Optional[str] = None,
) -> List[Dict]:
    """Filter IIP records by year and/or month."""
    records = get_iip_raw()["data"]
    result = []
    for r in records:
        if year and r.get("year") != int(year):
            continue
        if month and r.get("month", "").lower() != month.lower():
            continue
        result.append(r)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ASI queries
# ─────────────────────────────────────────────────────────────────────────────
def query_asi(year: Optional[str] = None) -> List[Dict]:
    """Filter ASI records by year."""
    records = get_asi_raw()["data"]
    if not year:
        return records
    return [r for r in records if _fuzzy_year_match(r.get("year", ""), year)]





# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────
def _fuzzy_year_match(record_year: str, query_year: str) -> bool:
    """Match year strings loosely — handles '2023-24', '2023', '23-24' etc."""
    ry = record_year.replace(" ", "").lower()
    qy = query_year.replace(" ", "").lower()
    return qy in ry or ry in qy or ry.startswith(qy) or qy.startswith(ry[:4])
