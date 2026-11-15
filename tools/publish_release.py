"""Publish a complete, checksummed draft only after every native build succeeded."""

import hashlib
import json
import os
import subprocess
from pathlib import Path
from package_release import ROOT, TARGETS, asset_name, project_version


def gh(*args, check=True):
    return subprocess.run(["gh", *args], check=check, capture_output=True, text=True)


def main():
    version = project_version()
    tag = os.environ["RELEASE_TAG"]
    if tag != "v" + version:
        raise ValueError("The release tag must match the application version")
    directory = ROOT / "release-assets"
    assets = [directory / asset_name(target) for target in TARGETS]
    sums = []
    for asset in assets:
        expected = asset.with_suffix(asset.suffix + ".sha256").read_text().split()[0]
        actual = hashlib.sha256(asset.read_bytes()).hexdigest()
        if expected != actual or asset.stat().st_size == 0:
            raise ValueError("Release artifact checksum mismatch: " + asset.name)
        sums.append(actual + "  " + asset.name)
    checksum_file = directory / "SHA256SUMS.txt"
    checksum_file.write_text("\n".join(sorted(sums)) + "\n")
    assets.append(checksum_file)
    expected_names = {p.name for p in assets}
    existing = gh("release", "view", tag, "--json", "isDraft,assets,url", check=False)
    if existing.returncode == 0:
        release = json.loads(existing.stdout)
        if not release["isDraft"]:
            if {a["name"] for a in release["assets"]} != expected_names:
                raise ValueError(
                    "Published release is incomplete; do not overwrite a public version"
                )
            print("Release already published:", release["url"])
            return
    else:
        gh(
            "release",
            "create",
            tag,
            "--verify-tag",
            "--draft",
            "--title",
            "Keypad Studio " + version,
            "--notes-file",
            str(ROOT / "docs/releases" / (tag + ".md")),
        )
    # Existing drafts are reversible and can recover from an interrupted upload.
    gh("release", "upload", tag, *(str(p) for p in assets), "--clobber")
    release = json.loads(gh("release", "view", tag, "--json", "isDraft,assets,url").stdout)
    sizes = {a["name"]: a["size"] for a in release["assets"]}
    if sizes != {p.name: p.stat().st_size for p in assets} or not release["isDraft"]:
        raise ValueError("Uploaded release assets did not verify; leaving the release unpublished")
    gh("release", "edit", tag, "--draft=false", "--latest")
    published = json.loads(gh("release", "view", tag, "--json", "isDraft,url").stdout)
    if published["isDraft"]:
        raise ValueError("Release was not published")
    print("Published:", published["url"])


if __name__ == "__main__":
    main()
