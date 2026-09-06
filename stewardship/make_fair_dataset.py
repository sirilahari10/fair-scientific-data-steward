"""
Transforms raw scientific telemetry into a self-describing, 
FAIR-compliant dataset with W3C PROV lineage and AI-readiness checks.
"""
import json
import hashlib
from datetime import datetime
import pandas as pd
import numpy as np

def calculate_checksum(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def audit_ai_readiness(df: pd.DataFrame) -> dict:
    """Evaluates whether dataset is clean and structured for ML ingestion."""
    total_cells = np.prod(df.shape)
    missing_ratio = float(df.isnull().sum().sum() / total_cells)
    
    return {
        "status": "PASS" if missing_ratio < 0.05 else "NEEDS_CURATION",
        "missingness_ratio": round(missing_ratio, 4),
        "feature_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "total_records": len(df)
    }

def generate_fair_digital_object(df: pd.DataFrame, dataset_id: str, creator_id: str):
    # 1. Capture Dataset & Integrity
    data_csv = df.to_csv(index=False).encode('utf-8')
    checksum = calculate_checksum(data_csv)
    ai_readiness = audit_ai_readiness(df)

    # 2. Machine-Actionable Schema (FAIR / JSON-LD / RO-Crate inspired)
    fdo_metadata = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@type": "Dataset",
        "@id": f"urn:uuid:{dataset_id}",
        "name": "Accelerator Beam Telemetry (Curated)",
        "dateCreated": datetime.utcnow().isoformat(),
        "creator": {"@type": "Person", "name": creator_id},
        "distribution": {
            "encodingFormat": "text/csv",
            "contentSize": f"{len(data_csv)} bytes",
            "sha256": checksum
        },
        # AI-Ready Metadata Annotation
        "ai_readiness_profile": ai_readiness,
        # W3C PROV Provenance Lineage
        "prov:wasGeneratedBy": {
            "@type": "prov:Activity",
            "name": "Automated_Normalization_and_Cleaning_Pipeline_v1.0",
            "endedAtTime": datetime.utcnow().isoformat()
        }
    }
    
    with open("dataset_metadata_fdo.json", "w") as f:
        json.dump(fdo_metadata, f, indent=2)
    
    print(f"FDO Package generated with SHA-256: {checksum}")
    print(f"AI Readiness Score: {ai_readiness['status']}")

if __name__ == "__main__":
    # Example raw experiment telemetry
    sample_df = pd.DataFrame({
        "beam_energy_gev": [11.98, 12.01, 11.95, np.nan, 12.04],
        "target_density": [0.98, 0.99, 0.97, 0.98, 0.99],
        "detector_count": [10450, 10520, 10390, 10410, 10600]
    })
    generate_fair_digital_object(sample_df, "beam-run-4021", "DataSteward_AI_Agent")
