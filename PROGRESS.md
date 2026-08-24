# Suivi du projet — Madagascar FireCarbon Tracker

Ce fichier sert à savoir, à tout moment, où on en est. Garde-le à la racine
du projet (`D:\DevWeb\TANDAVANALA\madagascar-firecarbon-tracker\PROGRESS.md`)
et je m'y référerai à chaque message.

---

## Phase 0 — Fondations & connexion DB — ✅ TERMINÉE ET VÉRIFIÉE
- [x] `app/core/config.py`
- [x] `app/core/database.py`
- [x] `app/main.py` (endpoint `/health`)
- [x] `tests/conftest.py`, `tests/test_health.py`
- [x] Vérifié chez toi : `pytest` → 2/2 passed, `/health` → `{"status":"ok","database":"connected"}`

## Phase 1 — Modèles PostgreSQL — ✅ TERMINÉE ET VÉRIFIÉE
- [x] `app/models/fire_detection.py`
- [x] `app/models/burned_area.py`
- [x] `app/models/alert.py`
- [x] `app/models/__init__.py`
- [x] `app/core/init_db.py`
- [x] `create_tables.py`
- [x] `tests/test_models.py`
- [x] Vérifié chez toi : `pytest` → 8/8 passed
- [x] Vérifié chez toi : `\dt` → `fire_detections`, `burned_areas`, `alerts` créées dans PostgreSQL réel
- [x] Bug résolu en cours de route : droits `GRANT ALL ON SCHEMA public` manquants (PostgreSQL 15+)

## Phase 2 — Repositories — ✅ TERMINÉE ET VÉRIFIÉE
- [x] `app/repositories/fire_repository.py`
- [x] `app/repositories/burned_area_repository.py`
- [x] `app/repositories/alert_repository.py`
- [x] `app/repositories/__init__.py`
- [x] `tests/test_repositories.py`
- [x] Vérifié chez toi : `pytest` → 16/16 passed

## Phase 3 — Service FIRMS (isolé, mockable) — ✅ TERMINÉE ET VÉRIFIÉE
- [x] `app/services/fire_data_source.py`
- [x] `app/services/__init__.py`
- [x] `tests/test_fire_data_source.py`
- [x] Vérifié chez toi : `pytest` → 21/21 passed

## Phase 4 — Job de polling FIRMS (toutes les 3-4h) — ✅ TERMINÉE ET VÉRIFIÉE
- [x] `app/jobs/poll_firms.py`
- [x] `tests/test_poll_firms.py`
- [x] `run_poll_firms_scheduler.py`
- [x] `requirements.txt` (+ APScheduler)
- [x] Vérifié chez toi : `pytest` → 25/25 passed

## Phase 5 — Endpoints fires/stats (lecture depuis PostgreSQL) — ✅ TERMINÉE ET VÉRIFIÉE
- [x] Schémas, routes, repositories, StaticPool
- [x] Vérifié chez toi : `pytest` → 35/35 passed

## Phase 6 — Service Google Earth Engine — ✅ TERMINÉE ET VÉRIFIÉE
- [x] Code testé (42/42) et identifiants GEE confirmés disponibles côté utilisateur

## Phase 7 — Endpoints carbone/alertes — 🔄 CODÉE ET TESTÉE ICI, À VÉRIFIER CHEZ TOI
- [x] `app/schemas/carbon.py`, `app/schemas/alert.py`, `app/schemas/__init__.py` (modifié)
- [x] `app/jobs/generate_alerts.py` (logique de seuils)
- [x] `app/api/routes/carbon.py`, `app/api/routes/alerts.py`
- [x] `app/main.py` modifié (2 routers de plus)
- [x] `tests/test_generate_alerts.py`, `tests/test_routes_carbon.py`, `tests/test_routes_alerts.py`
- [x] `run_generate_alerts_once.py`
- [x] Vérifié ici (bac à sable) : `pytest` → 49/49 passed
- [ ] **➜ PROCHAINE ACTION : toi, lancer `pytest` chez toi pour confirmer 49/49**
- [ ] **📌 Même limite connue qu'en Phase 6 : les alertes portent sur la zone "COFAV" entière, pas une région nommée précise**

## Phase 8 — Intégration frontend (remplacer les données mockées) — ⏳ PAS COMMENCÉE
## Phase 9 — Vérification bout-en-bout — ⏳ PAS COMMENCÉE

---

## Décisions en attente
- **Tests : SQLite (actuel) vs vraie base PostgreSQL de test** → on garde SQLite
  pour l'instant (statu quo), on y reviendra une fois les phases plus avancées.
