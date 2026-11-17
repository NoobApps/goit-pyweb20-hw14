import os
import sys

# 1. Додаємо кореневу папку проєкту в sys.path
sys.path.insert(0, os.path.abspath(".."))

project = "Contacts REST API"
copyright = "2026, Author"
author = "Author"
release = "1.0"

# 2. Підключаємо розширення autodoc (читання docstrings) та napoleon (підтримка Google/NumPy стилю)
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}

# 3. Заглушка для змінних середовища або зовнішніх клієнтів, щоб збірка не падала без запущеної БД/Redis
autodoc_mock_imports = [
    "redis",
    "cloudinary",
    "fastapi_mail",
]
# У docs/conf.py
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

def hide_secret_values(app, what, name, obj, options, lines):
    """Приховує реальні значення налаштувань у документації."""
    if "config" in name:
        lines.clear()

def setup(app):
    app.connect("autodoc-process-docstring", hide_secret_values)
    
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "uk"

# Тема оформлення (стандартна 'alabaster' або сучасніша 'nature' / 'classic')
html_theme = "alabaster"
html_static_path = ["_static"]