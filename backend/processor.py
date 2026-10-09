import os
import uuid
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple

_SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"

def process_upload(file_content: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
    """
    Saves the uploaded file, reads it via Pandas, and generates a summary.
    Returns (session_id, summary_dict).
    """
    session_id = str(uuid.uuid4())
    session_dir = _SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the file
    ext = os.path.splitext(filename)[1].lower()
    file_path = session_dir / f"original{ext}"
    
    with open(file_path, "wb") as f:
        f.write(file_content)
        
    # Read the dataset
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")

    # Generate basic stats
    num_rows, num_cols = df.shape
    columns = list(df.columns)
    
    # Data types and counts
    num_cols_list = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols_list = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols_list = df.select_dtypes(include=['datetime']).columns.tolist()
    
    missing_values = df.isnull().sum().to_dict()
    missing_cols_count = sum(1 for v in missing_values.values() if v > 0)
    
    duplicates = int(df.duplicated().sum())
    
    # Generate automatic summary
    summary_text = (
        f"This dataset contains {num_rows:,} records and {num_cols} variables. "
        f"There are {len(num_cols_list)} numerical, {len(cat_cols_list)} categorical, "
        f"and {len(date_cols_list)} date column(s). "
        f"{missing_cols_count} column(s) contain missing values."
    )
    
    # Build sample rows
    # Convert NaNs to None for valid JSON serialization
    df_sample = df.head(5).where(pd.notnull(df), None)
    sample_rows = df_sample.to_dict(orient="records")

    summary_dict = {
        "session_id": session_id,
        "filename": filename,
        "shape": {"rows": num_rows, "columns": num_cols},
        "columns": columns,
        "numerical_columns": num_cols_list,
        "categorical_columns": cat_cols_list,
        "date_columns": date_cols_list,
        "missing_values": missing_values,
        "duplicates": duplicates,
        "summary_text": summary_text,
        "sample_rows": sample_rows
    }
    
    # Save summary to session dir
    import json
    with open(session_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)
        
    return session_id, summary_dict

def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Retrieve the summary of a previously uploaded dataset."""
    summary_path = _SESSIONS_DIR / session_id / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Session {session_id} not found.")
    
    import json
    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)
