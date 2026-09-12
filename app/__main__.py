"""Run with python -m app from the repository root."""
import sys

def main():
    if sys.version_info < (3, 12):
        print("GBE requires Python 3.12 or newer.", file=sys.stderr)
        return 1
    try:
        import uvicorn
    except ImportError:
        print('Dependencies missing. Run: python -m pip install -e "."', file=sys.stderr)
        return 1
    print("Open http://127.0.0.1:8000 in your browser. Keep this window open.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
    return 0

if __name__ == "__main__":
    sys.exit(main())
