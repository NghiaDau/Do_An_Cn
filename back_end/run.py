import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def in_venv() -> bool:
    return Path(sys.prefix).resolve() == (ROOT / ".venv").resolve()


if __name__ == "__main__":
    # Chạy bằng Python hệ thống thì tự chạy lại bằng Python của .venv
    if not in_venv() and VENV_PYTHON.exists():
        sys.exit(subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], cwd=ROOT))

    import os

    import uvicorn

    HOST, PORT = "127.0.0.1", 8000
    os.environ["API_HOST"], os.environ["API_PORT"] = HOST, str(PORT)  # để main.py in link /docs
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
