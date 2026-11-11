"""Step 1 (task T1): download the two pinned snapshots of the Steam Games Dataset.

A = "current" snapshot, C = January 2024 snapshot, both taken from the Hugging Face
repository history. The commit hashes are fixed in src/steamcn/config.py, so every run
downloads exactly the same bytes. Files land in data/raw/ (not committed: too large).
"""
import shutil

import _bootstrap  # noqa: F401  (adds src/ to the import path)
from steamcn import config as cfg
from steamcn import paths


def main() -> None:
    # huggingface_hub downloads a file at a given commit and caches it locally.
    from huggingface_hub import hf_hub_download

    paths.RAW.mkdir(parents=True, exist_ok=True)
    for label, revision in (("a", cfg.REVISION_A), ("c", cfg.REVISION_C)):
        target = paths.RAW / f"games_{label}.csv"
        if target.exists():
            # Re-running is cheap: the pinned file never changes, so skip it.
            print(f"snapshot {label.upper()}: {target.relative_to(paths.ROOT)} already present")
            continue
        cached = hf_hub_download(
            repo_id=cfg.HF_DATASET, filename=cfg.HF_FILENAME, revision=revision, repo_type="dataset"
        )
        shutil.copyfile(cached, target)
        print(f"snapshot {label.upper()} ({revision[:8]}) -> {target.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()
