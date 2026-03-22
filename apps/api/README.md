# YasarNuri API

Yerel çalıştırma:

```bash
python -m venv .venv
pip install -e ".[dev]"
alembic upgrade head
uvicorn yasar_nuri_api.main:app --reload --host 0.0.0.0 --port 8000
```

`PROMPT_ASSETS_DIR` ortam değişkeni repodaki `packages/prompt_assets` klasörünü göstermelidir (Dockerfile içinde ayarlıdır).
