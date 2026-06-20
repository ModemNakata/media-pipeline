from __future__ import annotations

from pathlib import Path

import log
from config import AppConfig


def _clear_dest(s3_dest: str) -> None:
    log.info("upload", f"mc rm --recursive {s3_dest}")
    log.run_cmd(
        ["mc", "rm", "--recursive", "--force", s3_dest],
        module="upload",
    )

def upload_dir(cfg: AppConfig, local_dir: Path, s3_dest: str) -> None:
    _clear_dest(s3_dest)
    src = f"{local_dir}/"
    log.info("upload", f"mc cp --recursive {src} -> {s3_dest}")
    proc = log.run_cmd(
        ["mc", "cp", "--recursive", src, s3_dest],
        module="upload",
    )
    if proc.returncode != 0:
        log.info("upload", f"ERROR:\n{proc.stderr}")
        raise RuntimeError(f"mc upload failed for {local_dir}")
    total = sum(f.stat().st_size for f in local_dir.rglob("*") if f.is_file())
    print(f"[upload] done ({total / (1024*1024):.1f} MB uploaded)")


def upload_file(cfg: AppConfig, local_path: Path, s3_key: str) -> None:
    """Upload a single file to S3_BUCKET at the given key."""
    dest = f"{cfg.mc_alias}/{cfg.s3_bucket}/{s3_key}"
    log.info("upload", f"mc cp {local_path.name} -> {s3_key}")
    proc = log.run_cmd(
        ["mc", "cp", str(local_path), dest],
        module="upload",
    )
    if proc.returncode != 0:
        log.info("upload", f"ERROR:\n{proc.stderr}")
        raise RuntimeError(f"mc upload failed for {local_path}")
    size_mb = local_path.stat().st_size / (1024 * 1024)
    print(f"[upload] done ({size_mb:.1f} MB uploaded)")


def upload_video(cfg: AppConfig, output_dir: Path, content_id: str) -> None:
    dest = f"{cfg.mc_alias}/{cfg.s3_bucket}/videos/{content_id}/"
    upload_dir(cfg, output_dir, dest)


def upload_images(cfg: AppConfig, output_dir: Path, content_id: str) -> None:
    dest = f"{cfg.mc_alias}/{cfg.s3_bucket}/galleries/{content_id}/"
    upload_dir(cfg, output_dir, dest)
