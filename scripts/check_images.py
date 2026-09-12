import argparse
import json
import subprocess

LIMITS = {"api": 600 * 1024**2, "frontend": 128 * 1024**2}


def inspect_image(image):
    return json.loads(subprocess.check_output(["docker", "image", "inspect", image], text=True))[0]


def check_image(image, kind, sha):
    info = inspect_image(image)
    assert info["Size"] <= LIMITS[kind], f"Image {kind} trop volumineuse"
    assert info["Architecture"] == "amd64" and info["Os"] == "linux"
    assert info["Config"]["Labels"]["org.opencontainers.image.revision"] == sha
    assert info["Config"]["User"] == ("10001:10001" if kind == "api" else "101:101")
    return info["Size"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", required=True)
    p.add_argument("--frontend", required=True)
    p.add_argument("--sha", required=True)
    args = p.parse_args()
    print(json.dumps({kind: check_image(getattr(args, kind), kind, args.sha) for kind in LIMITS}))


if __name__ == "__main__":
    main()
