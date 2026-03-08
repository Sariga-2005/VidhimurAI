import json
from pathlib import Path
import sys

# Define the absolute path to VidhimurAI/backend
BACKEND_PATH = Path("c:/D/TBD/VidhimurAI/backend")
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

from app.services.kanoon_adapter import KanoonDoc

DATA_FILE = BACKEND_PATH / "app/data/kanoon_raw.json"

def validate():
    if not DATA_FILE.exists():
        print(f"Error: {DATA_FILE} does not exist.")
        return

    with open(DATA_FILE, encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error decoding JSON: {e}")
            return

    print(f"Found {len(data)} records. Validating schema...")
    
    valid_count = 0
    errors = []
    
    for i, item in enumerate(data):
        try:
            KanoonDoc(**item)
            valid_count += 1
        except Exception as e:
            errors.append(f"Record {i} (TID {item.get('tid')}): {e}")

    print(f"Validation complete: {valid_count}/{len(data)} valid.")
    
    if errors:
        print("\nErrors encountered:")
        for err in errors[:10]:  # Show first 10 errors
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more.")
    
    if valid_count == len(data) and len(data) >= 500:
        print("\nSUCCESS: Dataset is large and schema-compliant.")
    elif len(data) < 500:
        print(f"\nWARNING: Dataset size ({len(data)}) is below the target of 500.")
    else:
        print("\nFAILURE: Some records are invalid.")

if __name__ == "__main__":
    validate()
