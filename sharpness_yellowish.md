**Yes, both issues are fixable.** The yellowish tint and loss of crispness are very common with this kind of pipeline.

### 1. Yellowish Color Shift

This is almost always caused by missing or incorrect color metadata when converting to 10-bit. FFmpeg isn't properly tagging BT.709 color space.

**Best fix:** Use the `colorspace` filter early + explicit output color flags.

### 2. Maximum Crispness

To keep the image as sharp and detailed as possible:

- Lower the CRF (28 is too high for "high quality")
- Add **CAS** (Contrast Adaptive Sharpening) — currently one of the best sharpening filters
- Use better SVT-AV1 tuning (`sharpness`, QM, etc.)
- Slight improvements to the scaling filter

---

### Recommended Updated Command

```bash
ffmpeg -y -i input.mp4 \
  -vf "format=yuv420p10le:colorspace=bt709:range=tv,scale=1920:-2:flags=lanczos+accurate_rnd+full_chroma_int, \
       cas=0.78,drawtext=textfile=/tmp/tmp5ofj387m.txt:fontfile=BpmfHuninn-Regular.ttf:fontcolor=#7ccf00:fontsize=36:x=3:y=3:bordercolor=black:borderw=1" \
  -c:v libsvtav1 \
  -crf 23 \
  -preset 5 \
  -maxrate 6000k -bufsize 12000k \
  -pix_fmt yuv420p10le \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -fps_mode cfr \
  -svtav1-params "keyint=72:sharpness=2:enable-qm=1:qm-strength=11" \
  -c:a libopus -b:a 192k \
  -f webm output.webm
```

### Key Changes & Why

- **`format=...colorspace=bt709:range=tv`** + output color flags → should fix the yellowish tint
- **`cas=0.78`** → adds clean, modern sharpening (very effective)
- **CRF 23** (was 28) → much better detail retention
- **Preset 5** → better speed/quality balance than 4
- Increased bitrate ceiling (`6000k`) to allow more detail on complex scenes
- Added `sharpness=2`, `enable-qm=1`, and `qm-strength=11` for better texture preservation
- `accurate_rnd+full_chroma_int` on lanczos for higher quality scaling

---

### Quick Tuning Tips

**If it's still slightly yellowish:**
- Try changing `range=tv` to `range=pc` in both the format filter and `-color_range pc`

**For even more sharpness:**
- Increase `cas=0.85` to `cas=0.95` (can start to look artificial)
- Lower CRF to 21–22 (bigger files)
- Try `sharpness=3`

Would you like me to also give you a version using `zscale` (even better color/scaling quality) or `libplacebo` if your FFmpeg build supports them?

Just render a short sample with this command and tell me how it looks.

---

Yeah — a slight **yellow tint** usually points to a **color matrix / range mismatch**, not the encoder itself.

## 1) Yellowish output: most likely colorspace/range issue

For normal **SDR HD video**, you usually want:

- **Rec.709**
- **limited range** (`tv`)

If FFmpeg guesses wrong, the result can look a bit warm/yellow, washed, or slightly off.

### What to do
Make the colorspace explicit in the filter and in the output metadata.

If your source is standard HD SDR, try:

```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=1920:-2:flags=lanczos:in_color_matrix=bt709:out_color_matrix=bt709:in_range=tv:out_range=tv,drawtext=textfile=/tmp/tmp5ofj387m.txt:fontfile=BpmfHuninn-Regular.ttf:fontcolor=#7ccf00:fontsize=36:x=3:y=3:bordercolor=black:borderw=1" \
  -c:v libsvtav1 -crf 24 -preset 4 \
  -pix_fmt yuv420p10le \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a libopus -b:a 192k \
  -f webm output.webm
```

### If the source is full-range
If it’s screen capture or some webcam/PNG-style source, you may need `pc` instead of `tv`:

- `in_range=pc:out_range=pc`
- `-color_range pc`

### Best way to confirm
Check the source metadata:

```bash
ffprobe -hide_banner -show_streams input.mp4
```

Look for:
- `color_space`
- `color_transfer`
- `color_primaries`
- `color_range`

If those are missing or wrong, that’s likely the tint.

---

## 2) How to preserve the image as crisp as possible

### Biggest factors, in order:
1. **Don’t scale unless you have to**
   - If the source is already 1080p, skip the `scale` filter entirely.
   - Any rescale can soften a little.

2. **Lower CRF**
   - `CRF 28` is okay for efficient delivery, but not “highest quality.”
   - For crisper VOD, try **CRF 22–24**.

3. **Relax the bitrate cap**
   - `-maxrate 3125k` can force the encoder to flatten detail on busy scenes.
   - If this is VOD and not live, you can often **remove `-maxrate`/`-bufsize`** entirely, or raise them a lot.

4. **Use a high-quality scaler**
   - `lanczos` is already good.
   - If you want to go a bit sharper/cleaner, `zscale` is often excellent.

5. **Avoid over-sharpening**
   - Mild sharpening can help if the image feels soft.
   - Too much creates halos and ugly compression artifacts.

---

## My practical recommendation

For a quality-first VOD encode:

- **CRF 24**
- **remove or increase `maxrate`**
- **explicit bt709 color tagging**
- **skip scaling if already 1080p**

### If input is already 1080p
Use:

```bash
ffmpeg -y -i input.mp4 \
  -vf "drawtext=textfile=/tmp/tmp5ofj387m.txt:fontfile=BpmfHuninn-Regular.ttf:fontcolor=#7ccf00:fontsize=36:x=3:y=3:bordercolor=black:borderw=1" \
  -c:v libsvtav1 -crf 24 -preset 4 \
  -pix_fmt yuv420p10le \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a libopus -b:a 192k \
  -f webm output.webm
```

---

## Short version

- **Yellow tint** = usually **wrong color space/range**
- **Crispness** = mostly **lower CRF + no unnecessary scaling + less bitrate limiting**

If you want, paste the `ffprobe` output for the source file and I can tell you exactly which color settings you should use.
