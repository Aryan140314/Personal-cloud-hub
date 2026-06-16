from __future__ import annotations

from pathlib import Path


CATEGORY_EXTENSIONS = {
    "Documents": {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md"},
    "Coding": {
        ".py",
        ".java",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".css",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".sql",
    },
    "Images": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".svg"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Certificates": {".cer", ".crt", ".pem", ".pfx", ".p12"},
    "Projects": {".ipynb", ".fig", ".psd", ".ai", ".blend"},
}


def categorize_file(path: str | Path) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    filename = file_path.name.lower()

    if "certificate" in filename or "certification" in filename:
        return "Certificates"

    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category

    return "Other"
