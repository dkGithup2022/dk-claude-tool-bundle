"""template/ 을 새 프로젝트 폴더로 복사하고, 이름 package / PACKAGE_ 를 프로젝트 이름으로 바꾼다.

사용: python3 init_project.py --target <프로젝트 폴더> --pkg <파이썬 패키지 이름>
결과: 표준 출력에 JSON 한 줄 {"ok": true, "target": ..., "pkg": ..., "files": n} 또는 {"ok": false, "error": ...}
표준 라이브러리만 쓴다 (uv 환경이 생기기 전에 돈다).
"""

from __future__ import annotations

import argparse
import json
import keyword
import re
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[3] / "template"
IGNORE = shutil.ignore_patterns(".venv", "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache",
                                ".import_linter_cache", "uv.lock", ".package")
GUARD = ("pyproject.toml", "src", "plugin")  # 이 중 하나라도 있으면 이미 프로젝트가 있는 폴더
UV_PACKAGE_KEY = "package = true"  # pyproject.toml [tool.uv] 의 설정 키. 이름이 아니므로 바꾸지 않는다


def check_pkg(pkg: str) -> str | None:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,29}", pkg):
        return f"패키지 이름은 영문 소문자로 시작하고 영문 소문자·숫자·_ 만, 30자 이하로 쓴다: {pkg!r}"
    if keyword.iskeyword(pkg) or pkg in sys.stdlib_module_names:
        return f"파이썬 예약어나 표준 라이브러리 이름과 겹친다: {pkg!r}"
    return None


def check_target(target: Path) -> str | None:
    found = [name for name in GUARD if (target / name).exists()]
    return f"이미 프로젝트가 있는 폴더다 ({', '.join(found)} 있음): {target}" if found else None


def rename_text(text: str, pkg: str) -> str:
    keep = "\0UV_PACKAGE_KEY\0"
    text = text.replace(UV_PACKAGE_KEY, keep)
    text = re.sub(r"\bpackage\b", pkg, text)
    text = re.sub(r"\bPACKAGE_", pkg.upper() + "_", text)
    return text.replace(keep, UV_PACKAGE_KEY)


def copy_template(target: Path, pkg: str) -> int:
    shutil.copytree(TEMPLATE, target, ignore=IGNORE, dirs_exist_ok=True)
    (target / "src" / "package").rename(target / "src" / pkg)
    (target / "plugin" / "bin" / "package").rename(target / "plugin" / "bin" / pkg)
    count = 0
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        renamed = rename_text(text, pkg)
        if renamed != text:
            path.write_text(renamed, encoding="utf-8")
        count += 1
    return count


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True)
    p.add_argument("--pkg", required=True)
    a = p.parse_args()
    target = Path(a.target).expanduser().resolve()
    error = check_pkg(a.pkg) or check_target(target)
    if error:
        print(json.dumps({"ok": False, "error": error}, ensure_ascii=False))
        return 1
    target.mkdir(parents=True, exist_ok=True)
    files = copy_template(target, a.pkg)
    print(json.dumps({"ok": True, "target": str(target), "pkg": a.pkg, "files": files}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
