# Suivi du projet — Madagascar FireCarbon Tracker

## Phase 0 — Fondations & connexion DB — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 1 — Modèles PostgreSQL — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 2 — Repositories — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 3 — Service FIRMS (isolé, mockable) — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 4 — Job de polling FIRMS (toutes les 3-4h) — ✅ TERMINÉE ET VÉRIFIÉE

## Phase 4b — FIRMS multi-satellites (VIIRS + MODIS) — ✅ TERMINÉE ET VÉRIFIÉE AVEC DE VRAIES DONNÉES
- [x] Vérifié chez toi : `pytest` → 54/54 passed
- [x] Vérifié chez toi avec de vraies données : 372 détections cumulées sur 5 jours,
      dédoublonnage confirmé fonctionnel (168 → 66 nouvelles + 102 doublons filtrés)
- [x] Clé FIRMS confirmée saine (`current_transactions: 0`, largement sous la limite)
- [x] `day_range=7` spécifiquement échoue en 400 (entre 5 et 7 jours, cause exacte
      non isolée) — **sans impact pratique**, le scheduler réel utilise day_range=1
- [x] Config VSCode/Pylance clarifiée (faux positifs, pas de vrai bug)

## Phase 5 — Endpoints fires/stats (lecture depuis PostgreSQL) — ✅ TERMINÉE ET VÉRIFIÉE

## Phase 6 — Service Google Earth Engine — ✅ TERMINÉE ET VÉRIFIÉE AVEC DE VRAIES DONNÉES
- [x] 2 modes d'authentification + gestion collection vide — vérifié 54/54
- [x] **Découverte en conditions réelles** : MCD64A1 a un délai de publication
      réel d'environ **2-3 mois** (dernière image disponible ~juin 2026), pas
      5-16 jours comme supposé au départ.
- [x] Vérifié chez toi avec de vraies données (2025-08-01 -> 2025-12-01) :
      128 985 ha de surface brûlée détectée dans la zone COFAV
- [x] Vérifié chez toi sur la période la plus récente disponible (2026-04-01 ->
      2026-06-01) : 3 168,85 ha -- cohérent (moins d'activité hors pleine
      saison des feux, qui est plutôt juillet-novembre à Madagascar)
- [x] ⚠️ Facteur carbone (150 t/ha) : approximation générique, PAS encore calibrée
      avec des coefficients IPCC propres à la végétation du COFAV -- à affiner
      avant toute présentation officielle du chiffre exact à l'ONG
- [x] **📌 Important pour la présentation à l'ONG** : le dashboard "carbone estimé"
      aura toujours 2-3 mois de retard par rapport à aujourd'hui -- c'est une
      limite du satellite, pas du logiciel.
- [x] **📌 Limite connue à traiter plus tard : pas encore de rapprochement coordonnées → région nommée**
- [x] **📌 À faire avant la fin du stage : migrer vers un compte de service créé par l'ONG**

## Phase 6b — Sentinel-2 (surface brûlée, meilleure résolution) — 🔄 CODÉE ET TESTÉE ICI, À VÉRIFIER CHEZ TOI
- [x] `app/services/sentinel2_carbon_estimation_source.py` (dNBR, 2 modes d'auth)
- [x] `app/services/__init__.py` modifié
- [x] `tests/test_sentinel2_carbon_estimation_source.py` (6 tests)
- [x] `run_estimate_burned_area_once.py` modifié (+ `--source modis|sentinel2`)
- [x] Vérifié ici (bac à sable) : `pytest` → 60/60 passed
- [ ] **➜ PROCHAINE ACTION : toi, lancer `pytest` chez toi pour confirmer 60/60**
- [ ] **➜ Ensuite, tester en vrai : `python run_estimate_burned_area_once.py --source sentinel2 --period-start 2025-08-01 --period-end 2025-12-01`**
- [ ] **⚠️ Important pour la présentation : Sentinel-2 est une estimation indicative (seuil dNBR générique, non calibré sur le COFAV), à présenter comme complémentaire à MODIS, pas comme un remplacement scientifiquement validé**

## Phase 7 — Endpoints carbone/alertes — ✅ TERMINÉE ET VÉRIFIÉE
## Phase 8 — Intégration frontend (remplacer les données mockées) — ⏳ PAS COMMENCÉE
## Phase 9 — Vérification bout-en-bout — ⏳ PAS COMMENCÉE
## Phase 10 (nouvelle, gros chantier) — Stock de carbone / analyse végétation — ⏳ PAS COMMENCÉE (priorité 3 choisie)

---

## Décisions en attente
- Tests : SQLite (actuel, avec StaticPool) — décision prise, pas de changement prévu.

## Notes importantes
- Le projet n'est pas pour usage personnel : c'est pour une ONG. Les identifiants
  (GEE, etc.) doivent migrer vers un compte Google appartenant à l'ONG avant la
  fin du stage. Un README.md d'onboarding est à préparer (voir avec Claude).

## Audit de cohérence (dernière vérification complète)
- [x] 54/54 tests passent tous ensemble (aucune régression entre phases)
- [x] Chaque interface (5 au total) a une implémentation concrète + une factory
      `Depends()` — principe D respecté partout
- [x] `main.py` ne contient plus aucune logique métier, uniquement le branchement
      des routers + `/health`
- [x] Aucun import circulaire
- [x] `requirements.txt` couvre exactement toutes les bibliothèques utilisées
- [x] `.env.example` documente exactement toutes les variables lues par `config.py`
- [x] Aucune phase orpheline ou en double dans ce fichier
