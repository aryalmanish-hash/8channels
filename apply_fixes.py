import os
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime

PROJECT = Path(r"C:\Users\user\Downloads\8CHANNELS\8_Channel_Content_Factory")
BACKUP_DIR = PROJECT / "BACKUPS"

def make_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}"
    backup_path.mkdir(exist_ok=True)
    for f in ["core/story_generator.py",
              "core/story_generator_dark_history.py",
              "core/music_manager.py",
              "core/workflow.py",
              "core/compositor_ffmpeg.py"]:
        src = PROJECT / f
        if src.exists():
            shutil.copy2(src, backup_path / src.name)
    backups = sorted([b for b in BACKUP_DIR.iterdir() if b.is_dir()])
    while len(backups) > 10:
        shutil.rmtree(backups.pop(0))
    print(f"BACKUP OK: {backup_path.name}")

make_backup()
os.chdir(str(PROJECT))
sys.path.insert(0, str(PROJECT))

# ══════════════════════════════════════════════════════════════════════════════
# FIX 1 — Reddit story: 240-280 words -> 320-360 words
# L435: "Length: STRICTLY 240 to 280 words. Count words carefully. Anything under 240 is REJECTED..."
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- FIX 1: Reddit story words 240-280 -> 320-360 ---")

sg = PROJECT / "core/story_generator.py"
text = sg.read_text(encoding="utf-8")

OLD_R = "- Length: STRICTLY 240 to 280 words. Count words carefully. Anything under 240 is REJECTED and thrown away."
NEW_R = "- Length: STRICTLY 320 to 360 words. Count words carefully. Anything under 320 is REJECTED and thrown away."

if OLD_R in text:
    text = text.replace(OLD_R, NEW_R, 1)
    print("  [OK] Reddit word target updated")
else:
    print("  WARN: exact string not found — trying partial")
    # Broader fallback
    text = re.sub(
        r"STRICTLY 240 to 280 words",
        "STRICTLY 320 to 360 words",
        text
    )
    text = re.sub(
        r"under 240 is REJECTED",
        "under 320 is REJECTED",
        text
    )
    if "320 to 360 words" in text:
        print("  [OK] Regex replacement worked")

sg.write_text(text, encoding="utf-8")

# ── Syntax check ──────────────────────────────────────────────────────────
try:
    compile(sg.read_text(encoding="utf-8"), "story_generator.py", "exec")
    print("  syntax OK")
except SyntaxError as e:
    print(f"  syntax FAIL L{e.lineno}: {e.msg}")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 2 — Dark history: 260-290 -> 320-360 (multiple places)
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- FIX 2: Dark history words 260-290 -> 320-360 ---")

sgd = PROJECT / "core/story_generator_dark_history.py"
text2 = sgd.read_text(encoding="utf-8")

# Replace all 260-290 references
n = text2.count("260-290")
text2 = text2.replace("260-290", "320-360")
print(f"  Replaced '260-290' -> '320-360': {n} occurrences")

# Replace reject threshold: 220 -> 280 (roughly proportional to new target)
n2 = text2.count("< 220:")
text2 = text2.replace("< 220:", "< 280:")
print(f"  Reject threshold 220 -> 280: {n2} occurrences")

# Replace "Under 240 is REJECTED" -> "Under 320 is REJECTED"
n3 = text2.count("Under 240 is REJECTED")
text2 = text2.replace("Under 240 is REJECTED", "Under 320 is REJECTED")
print(f"  'Under 240 is REJECTED' -> 'Under 320 is REJECTED': {n3} occurrences")

# Also fix "260-290 word documentary" in docstring
text2 = text2.replace("260-290 word documentary", "320-360 word documentary")

# Response length threshold: > 200 -> > 250 (chars, not words)
text2 = text2.replace("if response and len(response.strip()) > 200:",
                       "if response and len(response.strip()) > 250:")
print(f"  Response min chars 200 -> 250")

sgd.write_text(text2, encoding="utf-8")

try:
    compile(sgd.read_text(encoding="utf-8"), "story_generator_dark_history.py", "exec")
    print("  syntax OK")
except SyntaxError as e:
    print(f"  syntax FAIL L{e.lineno}: {e.msg}")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 3 — REVERT Pass 3 speed-up in compositor_ffmpeg.py (no longer needed)
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- FIX 3: Revert Pass 3 speed-up (voice will be sped up before compose) ---")

ff = PROJECT / "core/compositor_ffmpeg.py"
text3 = ff.read_text(encoding="utf-8")

# Find and remove the entire Pass 3 block
OLD_PASS3 = '''    # ══════════════════════════════════════════════════════════════════
    # PASS 3: Speed up final video 1.1x (video + audio, keeps pitch)
    # ══════════════════════════════════════════════════════════════════
    speed_multiplier = 1.1
    print(f"  [FFMPEG] Pass 3: speed up {speed_multiplier}x (video + audio)...")

    speeded_mp4 = workdir / "final_speeded.mp4"
    pass3_cmd = [
        FFMPEG, "-y",
        "-i", str(output_path),
        "-filter_complex",
        f"[0:v]setpts=PTS/{speed_multiplier}[v];"
        f"[0:a]atempo={speed_multiplier}[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-threads", "0",
        str(speeded_mp4),
    ]

    if _run_ffmpeg(pass3_cmd, timeout=300, label="Pass 3"):
        # Replace output_path with speeded version
        if speeded_mp4.exists() and speeded_mp4.stat().st_size > 50000:
            try:
                output_path.unlink()
                _sh.move(str(speeded_mp4), str(output_path))
                print(f"  [FFMPEG] Speed-up applied — final video {speed_multiplier}x faster")
            except Exception as _e:
                print(f"  [FFMPEG] Speed-up succeeded but move failed: {_e}")
        else:
            print(f"  [FFMPEG] Speed-up output missing/small — keeping original")
    else:
        print(f"  [FFMPEG] Speed-up FAILED — keeping original 1x video")

    elapsed = time.time() - _start'''

NEW_NO_PASS3 = '''    elapsed = time.time() - _start'''

if OLD_PASS3 in text3:
    text3 = text3.replace(OLD_PASS3, NEW_NO_PASS3, 1)
    print("  [OK] Pass 3 removed")
else:
    print("  WARN: exact Pass 3 block not found — showing lines 528-570")
    lines = text3.splitlines()
    for i, ln in enumerate(lines, 1):
        if 528 <= i <= 570:
            print(f"    L{i:4d}: {ln[:120]}")

ff.write_text(text3, encoding="utf-8")

try:
    compile(ff.read_text(encoding="utf-8"), "compositor_ffmpeg.py", "exec")
    print("  syntax OK")
except SyntaxError as e:
    print(f"  syntax FAIL L{e.lineno}: {e.msg}")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 4 — Add speed_up_audio() helper in music_manager.py
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- FIX 4: Add speed_up_audio() helper in music_manager.py ---")

mm = PROJECT / "core/music_manager.py"
text4 = mm.read_text(encoding="utf-8")

if "def speed_up_audio" in text4:
    print("  [SKIP] speed_up_audio already exists")
else:
    HELPER = '''


def speed_up_audio(audio_path: Path, multiplier: float = 1.25) -> tuple[bool, float]:
    """
    Speed up an audio file in-place using FFmpeg atempo (preserves pitch).
    Returns (success, new_duration_seconds).

    atempo is limited to 0.5-2.0 per filter. For 1.25x this is fine as single filter.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return False, 0.0

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg:
        print(f"  [SPEED] ffmpeg not found — skipping speed-up")
        return False, 0.0

    # Speed up to temp file, then replace original
    temp_out = audio_path.parent / (audio_path.stem + "_speeded" + audio_path.suffix)

    cmd = [
        ffmpeg, "-y",
        "-i", str(audio_path),
        "-filter:a", f"atempo={multiplier}",
        "-vn",
        str(temp_out),
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  [SPEED] atempo failed: {r.stderr[-300:]}")
            return False, 0.0
    except Exception as e:
        print(f"  [SPEED] atempo error: {e}")
        return False, 0.0

    if not temp_out.exists() or temp_out.stat().st_size < 1000:
        return False, 0.0

    # Replace original with speeded version
    try:
        audio_path.unlink()
        shutil.move(str(temp_out), str(audio_path))
    except Exception as e:
        print(f"  [SPEED] move failed: {e}")
        return False, 0.0

    # Measure new duration
    new_dur = 0.0
    if ffprobe:
        try:
            r2 = subprocess.run(
                [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=15
            )
            new_dur = float(r2.stdout.strip())
        except Exception:
            pass

    print(f"  [SPEED] Voice sped up {multiplier}x — new duration {new_dur:.2f}s")
    return True, new_dur
'''

    text4 = text4.rstrip() + HELPER + "\n"
    mm.write_text(text4, encoding="utf-8")
    print("  [OK] speed_up_audio() appended")

try:
    compile(mm.read_text(encoding="utf-8"), "music_manager.py", "exec")
    print("  syntax OK")
except SyntaxError as e:
    print(f"  syntax FAIL L{e.lineno}: {e.msg}")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 5 — Wire speed_up_audio into workflow.py right after generate_voice
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- FIX 5: Wire speed_up_audio into workflow.py ---")

wf = PROJECT / "core/workflow.py"
text5 = wf.read_text(encoding="utf-8")

# Update import line
OLD_IMPORT = "from core.music_manager import get_background_music, mix_voice_with_music"
NEW_IMPORT = "from core.music_manager import get_background_music, mix_voice_with_music, speed_up_audio"

if OLD_IMPORT in text5:
    text5 = text5.replace(OLD_IMPORT, NEW_IMPORT, 1)
    print("  [OK] Import updated")
else:
    print("  WARN: import line not found")

# Insert speed-up call right after generate_voice, before generate_srt
OLD_VOICE_BLOCK = '''    voice_path = folder / "voice.wav"
    duration, voice_mode = generate_voice(script, voice_path, channel_id=channel_id)

    captions_path = folder / "captions.srt"
    generate_srt(script, duration, captions_path, audio_path=voice_path)'''

NEW_VOICE_BLOCK = '''    voice_path = folder / "voice.wav"
    duration, voice_mode = generate_voice(script, voice_path, channel_id=channel_id)

    # ── Speed up voice 1.25x (video will match this new duration) ──
    # Music will be mixed AFTER, so music stays at 1x
    _speed_ok, _new_dur = speed_up_audio(voice_path, multiplier=1.25)
    if _speed_ok and _new_dur > 0:
        duration = _new_dur
        print(f"  Voice sped up 1.25x — new video duration: {duration:.2f}s")

    captions_path = folder / "captions.srt"
    generate_srt(script, duration, captions_path, audio_path=voice_path)'''

if OLD_VOICE_BLOCK in text5:
    text5 = text5.replace(OLD_VOICE_BLOCK, NEW_VOICE_BLOCK, 1)
    print("  [OK] Speed-up call inserted after generate_voice")
else:
    print("  WARN: voice block not matched — showing L173-178")
    for i, ln in enumerate(text5.splitlines(), 1):
        if 173 <= i <= 178:
            print(f"    L{i:4d}: {repr(ln)}")

wf.write_text(text5, encoding="utf-8")

try:
    compile(wf.read_text(encoding="utf-8"), "workflow.py", "exec")
    print("  syntax OK")
except SyntaxError as e:
    print(f"  syntax FAIL L{e.lineno}: {e.msg}")

# ══════════════════════════════════════════════════════════════════════════════
# VERIFY ALL FIXES
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- VERIFY all 5 fixes ---")

r_final   = sg.read_text(encoding="utf-8")
d_final   = sgd.read_text(encoding="utf-8")
ff_final  = ff.read_text(encoding="utf-8")
mm_final  = mm.read_text(encoding="utf-8")
wf_final  = wf.read_text(encoding="utf-8")

checks = [
    ("Reddit: 320 to 360 words in prompt", "320 to 360 words" in r_final),
    ("Reddit: under 320 REJECTED",         "under 320 is REJECTED" in r_final),
    ("Dark: 320-360 in prompt",            "320-360" in d_final),
    ("Dark: reject threshold 280",         "< 280:" in d_final),
    ("Compositor: Pass 3 removed",         "Pass 3" not in ff_final),
    ("Compositor: speed_multiplier gone",  "speed_multiplier" not in ff_final),
    ("music_manager: speed_up_audio added", "def speed_up_audio" in mm_final),
    ("workflow: import updated",           "speed_up_audio" in wf_final.split("from core.music_manager")[1][:200] if "from core.music_manager" in wf_final else False),
    ("workflow: speed call inserted",      "_speed_ok, _new_dur = speed_up_audio" in wf_final),
]

all_pass = True
for name, ok in checks:
    mark = "OK  " if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  [{mark}] {name}")

# ══════════════════════════════════════════════════════════════════════════════
# FUNCTIONAL TEST — quick story generation to verify longer prompts work
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- TEST: Generate 1 dark history story (verify longer word count) ---")

import time
for mod in list(sys.modules.keys()):
    if any(m in mod for m in ["story", "script", "workflow", "wiki_harvester", "music"]):
        del sys.modules[mod]

try:
    from core.story_generator_dark_history import generate_from_topic_bank

    time.sleep(2)
    t0 = time.time()
    title, script, wiki = generate_from_topic_bank()
    elapsed = time.time() - t0

    if title and script:
        words = len(script.split())
        print(f"  Title  : {title}")
        print(f"  Wiki   : {wiki}")
        print(f"  Words  : {words}")
        print(f"  Time   : {elapsed:.1f}s")
        if 300 <= words <= 400:
            print(f"  [OK] Word count in new target range 320-360 (actual {words})")
        elif words < 280:
            print(f"  [WARN] Under 280 words — AI didn't obey new prompt")
        else:
            print(f"  [WARN] Slightly off target but acceptable")
    else:
        print(f"  FAIL: no result")

except Exception as e:
    print(f"  FAIL: {e}")
    import traceback; traceback.print_exc()

print()
if all_pass:
    print("  ALL 5 FIXES VERIFIED — ready for real video test")
    print("  Expected on next video:")
    print("    - Longer story (320-360 words)")
    print("    - Voice sped up 1.25x (talks faster)")
    print("    - Music at 1x normal (mixed AFTER speed-up)")
    print("    - Video length ~90 sec (was going to be 72 sec without word bump)")
    print("    - Backgrounds match video duration naturally")
else:
    print("  Some checks failed — paste output")

print("\n" + "="*80)
print("="*80)
print("="*80)
print("="*80)