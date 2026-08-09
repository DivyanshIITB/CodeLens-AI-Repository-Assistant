from pathlib import Path
from typing import Dict, Any, List
from backend.config.settings import settings

def build_file_tree(repo_path: Path) -> List[Dict[str, Any]]:
    def _scan_dir(current: Path) -> List[Dict[str, Any]]:
        items = []
        try:
            for entry in sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if entry.name in settings.EXCLUDED_DIRS or entry.name.startswith("."):
                    continue

                rel_path = entry.relative_to(repo_path).as_posix()
                if entry.is_dir():
                    children = _scan_dir(entry)
                    if children:
                        items.append({
                            "name": entry.name,
                            "path": rel_path,
                            "type": "directory",
                            "children": children
                        })
                elif entry.is_file():
                    if entry.suffix.lower() in settings.SUPPORTED_EXTENSIONS or entry.name.lower() in ("dockerfile", "makefile"):
                        items.append({
                            "name": entry.name,
                            "path": rel_path,
                            "type": "file",
                            "size": entry.stat().st_size
                        })
        except Exception:
            pass
        return items

    return _scan_dir(repo_path)

def get_file_content(repo_path: Path, relative_file_path: str) -> str:
    target = repo_path / relative_file_path
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"File not found: {relative_file_path}")
    return target.read_text(encoding="utf-8", errors="ignore")
