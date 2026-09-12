from pathlib import Path

from medinote.publication import build_public_bundle

if __name__ == "__main__":
    build_public_bundle(Path(__file__).resolve().parents[1])
