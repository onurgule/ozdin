# source_ingestion_tools

Önce API paketini düzenlenebilir kurun (modeller için):

```bash
cd apps/api
pip install -e .
```

Ardından:

```bash
cd packages/source_ingestion_tools
pip install -e .
set DATABASE_URL=postgresql+psycopg://...
set GEMINI_API_KEY=...
python -m source_ingestion_tools --format qa --path ../../docs/sample_data/sample_qa.jsonl
```
