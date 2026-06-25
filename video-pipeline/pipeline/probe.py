from __future__ import annotations

import json
import os
from dataclasses import dataclass

import log
from config import VideoConfig


@dataclass
class VideoMeta:
    width: int
    height: int
    bitrate_bps: int
    codec: str
    fps: float
    duration_s: float
    audio_bitrate_bps: int = 0
    audio_codec: str = ""
    source_size_bytes: int = 0
    sar_num: int = 1
    sar_den: int = 1

    @property
    def min_dim(self) -> int:
        return min(self.width, self.height)

    @property
    def is_portrait(self) -> bool:
        return self.height > self.width

    @property
    def source_size_mb(self) -> float:
        return self.source_size_bytes / (1024 * 1024)

    @property
    def display_width(self) -> int:
        """Display width accounting for sample aspect ratio (SAR)."""
        return int(round(self.width * self.sar_num / self.sar_den))

    @property
    def has_non_square_pixels(self) -> bool:
        return self.sar_num != 1 or self.sar_den != 1


def probe(cfg: VideoConfig) -> VideoMeta:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height,bit_rate,codec_name,r_frame_rate,sample_aspect_ratio",
        "-show_entries", "format=bit_rate,duration",
        "-of", "json",
        cfg.input_video,
    ]
    proc = log.run_cmd(cmd, module="probe")
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed:\n{proc.stderr}")

    try:
        data = json.loads(proc.stdout)
        s = data["streams"][0]
        fmt = data["format"]
        w = int(s["width"])
        h = int(s["height"])
        codec = s.get("codec_name", "unknown")
        num, den = str(s.get("r_frame_rate", "30/1")).split("/")
        fps = int(num) / int(den)
        br = s.get("bit_rate") or fmt.get("bit_rate", "0")
        br = int(br) if br not in ("N/A", "0") else 0
        dur = float(fmt.get("duration", 0))

        sar_str = s.get("sample_aspect_ratio", "")
        if sar_str and sar_str not in ("N/A", "0:0") and ":" in sar_str:
            parts = sar_str.split(":")
            sar_num = int(parts[0])
            sar_den = int(parts[1])
        else:
            sar_num = 1
            sar_den = 1
            sar_str = "1:1"
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError(f"failed to parse ffprobe output: {e}")

    audio_br = 0
    audio_codec = ""
    acmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=bit_rate,codec_name",
        "-of", "json",
        cfg.input_video,
    ]
    ap = log.run_cmd(acmd, module="probe")
    if ap.returncode == 0:
        try:
            adata = json.loads(ap.stdout)
            if adata.get("streams"):
                s2 = adata["streams"][0]
                abr = s2.get("bit_rate", "0")
                audio_br = int(abr) if abr not in ("N/A", "0") else 0
                audio_codec = s2.get("codec_name", "")
        except (KeyError, IndexError, ValueError):
            pass

    source_bytes = os.path.getsize(cfg.input_video)

    meta = VideoMeta(
        width=w, height=h, bitrate_bps=br, codec=codec,
        fps=fps, duration_s=dur,
        audio_bitrate_bps=audio_br, audio_codec=audio_codec,
        source_size_bytes=source_bytes,
        sar_num=sar_num, sar_den=sar_den,
    )

    probe_msg = f"{meta.width}x{meta.height} ({meta.min_dim}p)"
    if meta.has_non_square_pixels:
        probe_msg += (f"  [display {meta.display_width}x{meta.height}"
                      f"  sar={sar_str}]")
    probe_msg += (f"  {meta.codec}"
                  f"  {meta.bitrate_bps // 1000} kbps  {meta.fps:.2f} fps"
                  f"  {meta.duration_s:.1f}s"
                  f"  audio: {meta.audio_codec} {meta.audio_bitrate_bps // 1000}k"
                  f"  source: {meta.source_size_mb:.1f} MB")
    log.info("probe", probe_msg)
    return meta
