from pathlib import Path
import pandas as pd
def export_records(records, destination):
    pd.DataFrame([r.values for r in records]).to_excel(Path(destination), index=False)
