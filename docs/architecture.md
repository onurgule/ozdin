# Mimari özeti

- **İstemci**: Flutter (Android + Web), metin sohbeti; STT/TTS cihaz üzerinde.
- **API**: FastAPI, asenkron SQLAlchemy + PostgreSQL (pgvector) + Redis.
- **Akış**: soru → dil tespiti → (gerekirse) Türkçe sorgu yeniden yazma → hibrit FTS + vektör geri getirme → RRF birleştirme → isteğe bağlı LLM yeniden sıralama → eşik → kaynaklara bağlı yanıt üretimi → alıntı doğrulaması.

Gerçek kitap içeriği repoda yok; yerel içe aktarma ile yüklenir.
