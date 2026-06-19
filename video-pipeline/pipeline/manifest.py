from __future__ import annotations

from typing import Any

import log
from config import Profile


def generate(output_dir: str, profiles: list[Profile],
             actual_resolutions: dict[str, str],
             content_id: str) -> dict[str, str]:
    """Build the video_formats map: actual_resolution -> S3 key.

    This replaces the HLS master.m3u8 manifest.  The old HLS version
    is preserved below (revivable) in case HLS is ever needed again.
    """
    s3_prefix = f"videos/{content_id}"
    formats: dict[str, str] = {}
    for p in profiles:
        res = actual_resolutions.get(p.name, f"{p.ref_width}x?")
        formats[res] = f"{s3_prefix}/{p.name}.webm"
    log.info("manifest", f"video_formats: {formats}")
    return formats

# --- HLS revivable block -----------------------------------------------
# To switch back to HLS, uncomment the function below and comment the
# one above.  The transcode.py HLS flags must also be re-enabled.
#
# def generate(output_dir: str, profiles: list[Profile],
#              actual_resolutions: dict[str, str]) -> str:
#     lines = ["#EXTM3U", "#EXT-X-VERSION:7", ""]
#     for p in profiles:
#         res = actual_resolutions.get(p.name, f"{p.ref_width}x?")
#         lines.append(
#             f"#EXT-X-STREAM-INF:BANDWIDTH={p.bandwidth},RESOLUTION={res}\n"
#             f"{p.name}.m3u8\n"
#         )
#     content = "\n".join(lines)
#
#     path = os.path.join(output_dir, "master.m3u8")
#     with open(path, "w") as f:
#         f.write(content)
#     log.info("manifest", f"written: {path}")
#     return path
# -----------------------------------------------------------------------
