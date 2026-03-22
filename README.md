# YasarNuri

Kaynak temelli soru-cevap uygulaması: yalnızca sağlanan Yaşar Nuri Öztürk metinlerinden cevap verir.

## Gereksinimler

- Docker ve Docker Compose
- Python 3.12+ (yerel API geliştirme)
- Flutter stable (Android / Web)

## Hızlı başlangıç (Docker)

```bash
cp .env.example .env
# .env içinde GEMINI_API_KEY ve güvenli API_KEY değerlerini ayarlayın

docker compose -f infra/docker/docker-compose.yml up --build
```

API: `http://localhost:8000` — `GET /health`

Veritabanı migrasyonu (API konteyneri ilk çalıştırmada veya manuel):

```bash
docker compose -f infra/docker/docker-compose.yml exec api alembic upgrade head
```

## Örnek veri yükleme (sentetik)

Gerçek kitap metinleri repoya dahil değildir. Yerel JSONL örnekleri:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -e .
pip install -e ../../packages/source_ingestion_tools

# .env veya ortam değişkenleri: DATABASE_URL, GEMINI_API_KEY
python -m source_ingestion_tools ingest --format qa --path ../../docs/sample_data/sample_qa.jsonl
python -m source_ingestion_tools ingest --format quran --path ../../docs/sample_data/sample_quran.jsonl
```

## Yerel API (Docker olmadan)

PostgreSQL + Redis çalışıyor olmalı; `DATABASE_URL` ve `REDIS_URL` ayarlı olsun.

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e .
alembic upgrade head
uvicorn yasar_nuri_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Flutter (Android / Web)

```bash
cd apps/mobile_web_flutter
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000 --dart-define=API_KEY=change-me-in-production
```

Android için aynı `--dart-define` değerlerini kullanın; emülatörde `API_BASE_URL=http://10.0.2.2:8000` gerekebilir.

## Makefile hedefleri

| Hedef    | Açıklama              |
|----------|------------------------|
| `make up`   | Docker Compose ayağa kalkar |
| `make down` | Konteynerleri durdurur     |
| `make test` | API pytest                 |
| `make lint` | ruff + mypy + dart analyze |
| `make fmt`  | format                     |
| `make smoke` | `GET /health` duman testi (`SMOKE_API_BASE`, `SMOKE_API_KEY`) |

Duman testi (sohbet dahil): `RUN_SMOKE_ASK=1 python scripts/smoke_api.py`

## Proje yapısı

- `apps/mobile_web_flutter` — Flutter istemci
- `apps/api` — FastAPI sunucu
- `packages/shared_types` — API JSON şemaları
- `packages/prompt_assets` — sistem promptları
- `packages/source_ingestion_tools` — içe aktarma CLI
- `infra/docker` — Compose ve Dockerfile
- `docs` — mimari, örnek veri, boyut notları

## Güvenlik notu

Web derlemesinde `API_KEY` istemciye gömülür; üretimde hız sınırlama, WAF ve kısıtlı CORS kullanın. LLM anahtarı yalnızca sunucuda tutulur.
