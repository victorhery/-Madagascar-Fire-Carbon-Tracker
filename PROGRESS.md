# Suivi du projet — Madagascar FireCarbon Tracker

## Phase 0 — Fondations & connexion DB — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 1 — Modèles PostgreSQL — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 2 — Repositories — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 3 — Service FIRMS (isolé, mockable) — ✅ TERMINÉE ET VÉRIFIÉE

## Phase 4 — Job de polling FIRMS (toutes les 3-4h) — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 4b — FIRMS multi-satellites (VIIRS + MODIS) — ✅ TERMINÉE ET VÉRIFIÉE AVEC DE VRAIES DONNÉES
- [x] Vérifié chez toi : `pytest` → 54/54 passed
- [x] Re-testé le 31/08 avec `run_poll_firms_once.py --day-range 2/3/5` : dédoublonnage
      confirmé (102→204 créées cumulées, doublons correctement filtrés à chaque run)

## Phase 5 — Endpoints fires/stats (lecture depuis PostgreSQL) — ✅ TERMINÉE ET VÉRIFIÉE

## Phase 6 — Service Google Earth Engine (MODIS) — ✅ TERMINÉE ET VÉRIFIÉE AVEC DE VRAIES DONNÉES
- [x] 2 modes d'authentification + gestion collection vide
- [x] Délai de publication réel MODIS ~2-3 mois (dernière image dispo ~juin 2026)
- [x] ⚠️ Facteur carbone (150 t/ha) : approximation générique, pas calibrée IPCC

## Phase 6b — Sentinel-2 (surface brûlée, meilleure résolution) — ✅ CODÉE ET TESTÉE
- [x] `app/services/sentinel2_carbon_estimation_source.py` (dNBR, 2 modes d'auth)
- [x] `run_estimate_burned_area_once.py --source sentinel2` opérationnel
- [ ] **⚠️ Seuil dNBR générique, non calibré sur le COFAV** — à traiter avant présentation officielle

## Phase 7 — Endpoints carbone/alertes — ✅ TERMINÉE ET VÉRIFIÉE

## Phase 8 — Intégration frontend (remplacer les données mockées) — 🔄 EN COURS
- [x] `services/statsService.ts`, `carbonService.ts`, `alertService.ts` créés
- [x] `useDashboardStats.ts` branché sur `/api/v1/stats` (mock supprimé)
- [x] `RecentEventsTable.vue` branché sur `/api/v1/carbon/estimates`, badge source MODIS/Sentinel-2
- [x] `fireService.ts` + `FireLeafletMap.vue` déjà branchés depuis Phase 5
- [x] **Fix critique 31/08** : `stats.totals()` sommait TOUT l'historique `burned_areas`
      sans filtre → les runs de test Phase 6/6b s'accumulaient et gonflaient le total
      affiché (285 848,8 ha / 42 877 313,8 t constaté = juste la somme de tous les
      tests passés, pas une mesure réelle actuelle)
- [x] **Multi-satellite (31/08)** : colonne `source` ajoutée à `BurnedArea` ; le
      dashboard affiche désormais, PAR RÉGION, le dernier résultat connu — Sentinel-2
      toujours préféré à MODIS quand les deux existent (`latest_by_region()` /
      `totals_latest_per_region()`), décision produit confirmée avec l'utilisateur
- [x] `run_estimate_burned_area_scheduler.py` créé : automatise MODIS (fenêtre 120j)
      + Sentinel-2 (fenêtre 21j) toutes les 24h, tague chaque run avec sa source
- [ ] **➜ PROCHAINE ACTION (toi) : `pytest` chez toi pour confirmer que tout passe**
      avec les nouveaux fichiers (fix totals + colonne source + tests associés)
- [ ] **➜ Migration DB requise** : la colonne `source` sur `burned_areas` n'existe
      pas encore sur ta base Postgres existante (pas d'Alembic dans ce projet).
      Lancer manuellement :
      `ALTER TABLE burned_areas ADD COLUMN source VARCHAR NOT NULL DEFAULT 'modis';`
- [ ] **➜ Décision à prendre** : lancer `run_estimate_burned_area_scheduler.py` en
      permanence (3e terminal, en plus de l'API et de `run_poll_firms_scheduler.py`)
      ou l'intégrer autrement (cron, service systemd/Windows Task Scheduler) avant
      la présentation à l'ONG — un scheduler qui ne tourne que pendant que ton
      terminal est ouvert n'est pas une vraie automatisation en production
- [ ] `alertService.ts` créé mais pas encore affiché dans un composant du dashboard
- [ ] Aucune notification/rafraîchissement live côté frontend (le dashboard ne se
      recharge pas tout seul quand une nouvelle estimation arrive — pour l'instant
      il faut recharger la page ; un polling périodique ou WebSocket serait la suite
      logique une fois le scheduler backend validé)

## Phase 9 — Vérification bout-en-bout — ⏳ PAS COMMENCÉE
## Phase 10 (nouvelle, gros chantier) — Stock de carbone / analyse végétation — ⏳ PAS COMMENCÉE (priorité 3 choisie)

---

## Décisions en attente
- Tests : SQLite (actuel, avec StaticPool) — décision prise, pas de changement prévu.
- ✅ Résolu (31/08) : quand MODIS et Sentinel-2 couvrent la même région, le dashboard
  affiche toujours Sentinel-2 s'il existe, sinon MODIS (décision utilisateur).
- Ouvert : comment faire tourner `run_estimate_burned_area_scheduler.py` en continu
  en dehors d'un terminal ouvert manuellement (service Windows / cron / conteneur) ?
- Ouvert : rafraîchissement automatique du dashboard côté frontend (polling ? à quel
  intervalle ?) — actuellement l'utilisateur doit recharger la page.

## Notes importantes
- Le projet n'est pas pour usage personnel : c'est pour une ONG. Les identifiants
  (GEE, etc.) doivent migrer vers un compte Google appartenant à l'ONG avant la
  fin du stage. Un README.md d'onboarding est à préparer (voir avec Claude).
- `BurnedArea` et `Alert` n'ont toujours pas de rapprochement coordonnées → région
  nommée (limite connue depuis Phase 6/7, non traitée).

## Audit de cohérence (dernière vérification complète : avant le fix du 31/08 — À REFAIRE)
- [x] 60/60 tests passaient tous ensemble avant les changements du 31/08
- [ ] **À revérifier chez toi après ce lot de fichiers** (nouveaux tests ajoutés :
      totals since, latest_by_region, source sur estimate_burned_area)
- [x] Chaque interface a une implémentation concrète + une factory `Depends()`
- [x] `main.py` ne contient toujours aucune logique métier
- [x] Aucun import circulaire détecté dans les fichiers modifiés
