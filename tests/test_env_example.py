import re
from pathlib import Path

from config import env

ROOT = Path(__file__).resolve().parents[1]


def example_names() -> set[str]:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Z][A-Z0-9_]*)=", text, flags=re.MULTILINE))


def test_every_setting_variable_is_in_env_example():
    import importlib

    from config import settings

    importlib.reload(settings)
    missing = env.USED - example_names()
    assert not missing, f"Add to .env.example: {sorted(missing)}"


def test_env_example_has_no_real_secret():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert re.search(r"^DJANGO_SECRET_KEY=$", text, flags=re.MULTILINE)


def test_settings_code_reads_the_environment_only_through_the_helper():
    allowed = {"env.py", "manage.py", "wsgi.py", "asgi.py"}
    for path in (ROOT / "src" / "backend").rglob("*.py"):
        if path.name in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        assert "os.environ" not in text and "os.getenv" not in text, str(path)
