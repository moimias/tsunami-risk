Nom: TsunamiWatch

Utilisateur : un analyste en gestion des risques côtiers, par exemple dans un service de protection civile.
Problème : il doit décider où concentrer ses moyens de surveillance, mais il n’a pas de vue simple de la fréquence des séismes capables de provoquer un tsunami.
Décision : prioriser les zones à surveiller en premier.
Question centrale : quelles zones du globe (cellules de 5°×5°) ont la plus forte probabilité d’au moins un séisme potentiellement tsunamigène (magnitude ≥ 6,5, profondeur ≤ 70 km) dans les 10 prochaines années ?
Périmètre : séismes de magnitude ≥ 6,0 depuis 1990 (source USGS). Sont exclus les tsunamis d’origine volcanique ou liés à des glissements de terrain. Fréquence utile : mise à jour mensuelle.

Cas d’usage et KPI

Cas 1
En tant qu’analyste en gestion des risques côtiers,
je veux classer les zones par fréquence de séismes tsunamigènes,
afin de décider quelles zones surveiller en priorité.
KPI : taux annuel d’événements candidats par cellule (annual_rate).

Cas 2
En tant que responsable de planification,
je veux connaître la probabilité d’au moins un séisme tsunamigène sur 10 ans dans chaque zone,
afin de justifier des investissements de prévention à long terme.
KPI : probabilité à 10 ans (prob_10y), calculée par la loi de Poisson.

Cas 3
En tant qu’analyste,
je veux savoir quelle part des séismes d’une zone est superficielle,
afin de repérer les zones où les séismes sont les plus susceptibles de déplacer le fond marin.
KPI : pourcentage de séismes avec is_shallow vrai par cellule.

Au tableau « cas d’usage, KPI, données nécessaires, fréquence » du sujet, vous pouvez ajouter ces colonnes :

Cas 1 : annual_rate, magnitude, profondeur, coordonnées, mise à jour mensuelle.
Cas 2 : prob_10y, mêmes champs, mise à jour mensuelle.
Cas 3 : % is_shallow, profondeur et coordonnées, mise à jour mensuelle(amélioration).





# Estimation probabiliste du risque de tsunami (données sismiques USGS)

**Question centrale** : Quelles zones géographiques (cellules de 5°×5°) ont la plus forte probabilité d'au moins un séisme potentiellement tsunamigène (M ≥ 6,5, profondeur ≤ 70 km) dans les 10 prochaines années ?
**Utilisateur** : analyste en gestion des risques côtiers. **Décision** : prioriser les zones à surveiller.

## Source et conditions
USGS Earthquake Catalog (API FDSN) — https://earthquake.usgs.gov/fdsnws/event/1/ — données publiques, sans clé. Date d'accès : 7 novembre 2026 (fichier `source_20261107T215457Z.json`, 5 535 séismes de magnitude ≥ 6,0 depuis 1990).

## Installation et exécution
```
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python src/pipeline.py --collect   # télécharge USGS puis lance tout
python src/pipeline.py             # rejeu sur le dernier fichier raw (hors-ligne)
python tests/test_quality.py       # tests des règles de qualité
```
Sans Internet : `python src/pipeline.py` utilise `data/raw/sample_source.json` (données synthétiques).

## Arborescence
`data/raw` (copie brute) · `data/curated` (dataset.csv, risk_by_cell.csv) · `data/rejected` (rejets + cause) · `reports` (profile.json, run_report.json) · `config/data_contract.yaml` · `src` · `tests`.

## Règles de qualité
R1 event_id renseigné · R2 date valide · R3 magnitude 0–10 · R4 coordonnées valides · R5 profondeur −5–800 km (rejet) · R6 event_id unique (déduplication) · R7 fraîcheur du fichier ≤ 7 jours (alerte).

## Idempotence
Upsert par clé métier `event_id` + écriture atomique des CSV : relancer ne crée aucun doublon (`new_rows_added_to_curated = 0`).

## Modèle
Processus de Poisson par cellule : λ = nb d'événements candidats / durée du catalogue ; P(≥1 en T ans) = 1 − exp(−λT).

## Limites connues
Catalogue court (≈35 ans) face aux périodes de retour des grands tsunamis ; séisme sous-marin non vérifié (pas de masque terre/mer) ; hors glissements de terrain et volcans ; grille 5° grossière ; Poisson suppose l'indépendance des événements (pas de répliques/clusters). Amélioration : seconde source NOAA NCEI (tsunamis historiques) et SQLite avec contrainte UNIQUE.
 Avec 35 ans de données et des cellules de 5°, la probabilité à 10 ans sature près de 1 dans les zones les plus actives : le classement par `annual_rate` est plus informatif que `prob_10y`.