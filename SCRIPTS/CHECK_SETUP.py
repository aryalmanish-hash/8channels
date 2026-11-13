from __future__ import annotations

from core.system_checks import check_system, write_health_report

report = check_system()
print("8-Channel Content Factory Setup Check")
print("====================================")
print("Python:", report["python"])
for pkg in report["packages"]:
    print(f"{pkg['import']}:", "OK" if pkg["ok"] else "MISSING", f"({pkg['package']})")
print("ffmpeg:", "OK" if report["ffmpeg"]["ok"] else "MISSING")
print("dashboard ready:", "YES" if report["ready_for_dashboard"] else "NO")
print("tts ready:", "YES" if report["ready_for_tts"] else "NO")
print("mp4 render ready:", "YES" if report["ready_for_mp4_render"] else "NO")
path = write_health_report()
print("\nHealth report written to:", path)
print("\nIf packages are missing, run:")
print("pip install -r requirements.pip")
print("\nIf ffmpeg is missing, install FFmpeg and add it to PATH.")
