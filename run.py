"""Single entry point for the whole project.

    python run.py data     # download pinned snapshots A and C, trim to the needed columns
    python run.py tables   # clean + build the analysis tables (CSV + one XLSX workbook)
    python run.py all      # everything, end to end (this is the working pilot)

Every step reads its inputs from data/ with pandas.read_csv and writes its outputs
back to data/processed/, so any step can be re-run on its own.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = {
    "data": ["scripts/00_download.py", "scripts/01_trim.py"],
    "tables": ["scripts/02_build_tables.py"],
    "eda": ["scripts/03_eda.py"],
    "sq1": ["scripts/04_sq1.py"],
    "sq2": ["scripts/05_sq2.py"],
    "sq3": ["scripts/06_sq3.py"],
}
ALL = ["data", "tables", "eda", "sq1", "sq2", "sq3", "report"]


def run_step(name: str) -> None:
    if name == "test":
        sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=ROOT))
    if name == "report":
        print("report: not implemented yet (task T8: quarto render report/report.qmd)")
        return
    if name == "app":
        sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", "app/app.py"], cwd=ROOT))
    for script in STEPS[name]:
        path = ROOT / script
        if not path.exists():
            print(f"{name}: {script} not implemented yet")
            continue
        print(f"== {script}")
        subprocess.check_call([sys.executable, str(path)], cwd=ROOT)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for step in ALL:
            run_step(step)
    elif target in STEPS or target in {"test", "report", "app"}:
        run_step(target)
    else:
        sys.exit(f"unknown target '{target}'. Use one of: {', '.join(ALL + ['app', 'test', 'all'])}")
