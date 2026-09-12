from pathlib import Path

from medinote.config import Settings
from medinote.main import create_app
from medinote.serialization import write_json


def main():
    root = Path(__file__).resolve().parents[1]
    write_json(
        root / "contracts/openapi.json", create_app(Settings(root=root, env="test")).openapi()
    )


if __name__ == "__main__":
    main()
