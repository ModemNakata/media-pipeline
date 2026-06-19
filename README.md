# ff-s3-pipeline

Media processing pipeline that downloads source files from S3 (MinIO), transcodes them, and uploads results with API status callbacks.

## Quality Settings

### Video encoding (multi-resolution .webm / AV1)

| Setting | Value | Notes |
|---------|-------|-------|
| Codec | libsvtav1 | |
| CRF | 28 (1080p), 30 (720p), 32 (480p) | Lower = better quality |
| Preset | 4 | Balances speed vs quality-per-bitrate |
| Pixel format | yuv420p10le | 10-bit for banding reduction |
| Audio | libopus @ 192k | Stereo, transparent |
| Rate control | +25% over previous defaults | 3125k (1080p), 1875k (720p), 1000k (480p) |
| svtav1-params | `keyint=3s:scd=1:film-grain=0:film-grain-denoise=0` | Lanczos resampling for sharper scaling |

### Image encoding (AVIF)

| Setting | Value | Notes |
|---------|-------|-------|
| Quality | 85 | Visually lossless for most content |
| Thumbnail CRF | 27 | |
| Preview CRF | 32 | 640x360 WebM clip |
| Image preview CRF | 27 | 720px square crop |

### Recent improvements

- **HLS → multi-resolution WebM**: Output is now a `.webm` file per resolution profile instead of HLS fMP4 segments + playlists. HLS code preserved as revivable comments.
- **Quality bump**: CRF lowered by 2 per tier, rate control raised 25%, preset relaxed to 4, Lanczos scaling, audio bitrate doubled to 192k.
- **source_resolution**: Pipeline now reports original `WxH` via PATCH for database storage.
