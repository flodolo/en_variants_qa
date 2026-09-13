import sys

from pathlib import Path


# Add .../scripts to sys.path so tests can do "import check_en_differences"
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "scripts"))
