#!/usr/bin/env python3
"""tools/rename_roles.py

一次性迁移脚本：把全课资料库里的角色称呼从
    听讲者 -> 学员
    分享者 -> 讲师
统一过来。同时处理文件名、目录名和内部链接。

执行顺序：
  Phase A  在所有 .md/.py/.json/.html/.bat/.ps1/.txt 内容里做文本替换
  Phase B  对文件名与目录名做同样的替换（自底向上）

脚本是幂等的：再次运行不会产生额外变化。
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # 课程资料库/

# 顺序敏感：更长的短语放前面，避免部分替换造成歧义
TEXT_REPLACEMENTS: list[tuple[str, str]] = [
    ("分享者手册", "讲师手册"),
    ("分享者画像", "讲师画像"),
    ("听讲者画像", "学员画像"),
    ("分享者反馈", "讲师反馈"),
    ("分享者分享风格指南", "讲师风格指南"),
    ("分享者授课脚本规范", "讲师授课脚本规范"),
    ("听讲者", "学员"),
    ("分享者", "讲师"),
]

CONTENT_EXTS = {".md", ".py", ".json", ".html", ".bat", ".ps1", ".txt"}

# 跳过的目录（输出产物 / 第三方 / VCS）
SKIP_DIR_NAMES = {
    ".playwright-mcp",
    "output",
    "book_reading_package",
    "html_reading_package",
    ".git",
    "__pycache__",
}


def replace_text(text: str) -> tuple[str, int]:
    count = 0
    for old, new in TEXT_REPLACEMENTS:
        if old in text:
            count += text.count(old)
            text = text.replace(old, new)
    return text, count


def should_process_file(path: Path) -> bool:
    if path.suffix.lower() not in CONTENT_EXTS:
        return False
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return False
    return True


def rename_needed(name: str) -> str | None:
    new_name = name
    for old, new in TEXT_REPLACEMENTS:
        if old in new_name:
            new_name = new_name.replace(old, new)
    return new_name if new_name != name else None


def phase_a_replace_text() -> tuple[int, int]:
    files_changed = 0
    total_replacements = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if not should_process_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="utf-8-sig")
            except Exception as exc:  # pragma: no cover - defensive
                print(f"SKIP (encode error): {path}: {exc}")
                continue
        new_text, n = replace_text(text)
        if n > 0:
            path.write_text(new_text, encoding="utf-8")
            rel = path.relative_to(ROOT)
            print(f"EDIT  [{n:3d}x] {rel}")
            files_changed += 1
            total_replacements += n
    return files_changed, total_replacements


def phase_b_rename_paths() -> list[tuple[Path, Path]]:
    renamed: list[tuple[Path, Path]] = []
    # 自底向上遍历，先改文件再改父目录，避免路径失效
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
        # 跳过排除目录
        if any(skip in Path(dirpath).parts for skip in SKIP_DIR_NAMES):
            continue
        for fn in filenames:
            new_fn = rename_needed(fn)
            if new_fn:
                src = Path(dirpath) / fn
                dst = Path(dirpath) / new_fn
                if dst.exists():
                    print(f"CONFLICT: {src.relative_to(ROOT)} -> {new_fn} (目标已存在，跳过)")
                    continue
                src.rename(dst)
                renamed.append((src, dst))
        for dn in dirnames:
            if dn in SKIP_DIR_NAMES:
                continue
            new_dn = rename_needed(dn)
            if new_dn:
                src = Path(dirpath) / dn
                dst = Path(dirpath) / new_dn
                if dst.exists():
                    print(f"CONFLICT: {src.relative_to(ROOT)} -> {new_dn} (目标已存在，跳过)")
                    continue
                src.rename(dst)
                renamed.append((src, dst))
    for src, dst in renamed:
        print(f"RENAME {src.relative_to(ROOT)}  ->  {dst.name}")
    return renamed


def main() -> None:
    print(f"ROOT = {ROOT}\n")
    print("=== Phase A: 文本替换 ===")
    files_changed, total = phase_a_replace_text()
    print(f"\nPhase A done: {files_changed} 个文件修改，共 {total} 处替换\n")

    print("=== Phase B: 文件/目录重命名 ===")
    renamed = phase_b_rename_paths()
    print(f"\nPhase B done: {len(renamed)} 个路径重命名\n")

    print("全部完成。如需回滚，请用 git 恢复。")


if __name__ == "__main__":
    main()
