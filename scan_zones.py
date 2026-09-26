"""一次性排查工具：扫描渲染图里的纵向死区。

白卡内、底栏以上的区域如果出现连续 >=60px 完全没有墨迹的横带，
说明版面留了一块空洞。超过 170px 会被当成需要处理的问题。
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))


def bands(path, top=38, bottom=1080 - 38 - 86, left=38, right=1080 - 38, limit=60):
    gray = np.array(Image.open(path).convert("L"))
    inner = gray[top:bottom, left:right]
    ink = (inner < 240).sum(axis=1) > 0
    found, start = [], None
    for i, has_ink in enumerate(ink):
        if has_ink:
            if start is not None:
                found.append((start + top, i - start))
                start = None
        elif start is None:
            start = i
    if start is not None:
        found.append((start + top, len(ink) - start))
    return [b for b in found if b[1] >= limit]


def main():
    entrypoints = [
        "cover_v2.py",
        "render_camera_basics.py",
        "render_codex55.py",
        "render_map_collection.py",
        "render_promo_music.py",
        "render_winrar_unified.py",
        "render_workbuddy.py",
    ]
    worst_overall = 0
    with tempfile.TemporaryDirectory() as root:
        for name in entrypoints:
            out = Path(root) / name.replace(".py", "")
            out.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [sys.executable, name, "--out", str(out)],
                check=True,
                capture_output=True,
            )
            print(f"--- {name} ---")
            for page in sorted(out.glob("*.png")):
                found = bands(page)
                worst = max((length for _, length in found), default=0)
                worst_overall = max(worst_overall, worst)
                flag = "  <== VOID" if worst > 170 else ""
                print(f"  {page.name} worst={worst:4d}px{flag} {found if found else ''}")
    print(f"\nworst band across all pages: {worst_overall}px")


if __name__ == "__main__":
    main()
