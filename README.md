# Relais « éclairs » pour l'app Météo

Toutes les 10 minutes, GitHub Actions lance `fetch_lightning.py`, qui :

1. télécharge les éclairs détectés par le satellite **Meteosat Third Generation** (EUMETSAT,
   produit *LI Level 2 Lightning Flashes*) sur les **3 dernières heures** ;
2. garde ceux situés au-dessus de la France (zone modifiable) ;
3. publie un petit fichier `lightning.json` sur la branche `data` du dépôt.

L'app lit ce fichier et affiche les éclairs sur la carte radar.

## Mise en place (une seule fois)

### 1. Compte EUMETSAT (gratuit)
1. Créez un compte sur **https://eoportal.eumetsat.int/** et validez l'e-mail.
2. Récupérez vos identifiants d'API sur **https://api.eumetsat.int/api-key/** (connecté à votre compte) :
   une **Consumer Key** et un **Consumer Secret**.

### 2. Dépôt GitHub
1. Créez un compte sur **https://github.com** si besoin, puis un **nouveau dépôt public**
   (par exemple `eclairs-meteo`). Public = minutes GitHub Actions gratuites et illimitées.
2. Déposez-y les fichiers de ce dossier en conservant l'arborescence :
   `fetch_lightning.py`, `requirements.txt`, `README.md` et `.github/workflows/lightning.yml`
   (bouton *Add file › Upload files* ; le dossier `.github` doit être glissé en entier).
3. *Settings › Secrets and variables › Actions › New repository secret* : créez
   - `EUMETSAT_CONSUMER_KEY` = votre Consumer Key
   - `EUMETSAT_CONSUMER_SECRET` = votre Consumer Secret
4. Onglet *Actions* : activez les workflows si GitHub le demande, ouvrez « Éclairs MTG »
   puis *Run workflow* pour un premier lancement manuel. Il doit se terminer en vert.

### 3. Adresse à saisir dans l'app
```
https://raw.githubusercontent.com/<votre-compte>/<votre-dépôt>/data/lightning.json
```
Dans l'app : section « Radar des précipitations » › ligne « Éclairs » › coller l'adresse.

## Bon à savoir
- **Ce qui est détecté** : tous les éclairs (nuage-sol, dans les nuages, entre nuages),
  vus depuis l'espace ; précision de l'ordre de 5 km. Ce ne sont pas uniquement des impacts au sol.
- **Délai** : quelques minutes entre l'éclair et sa publication par EUMETSAT, plus le rythme
  du relais (10 min, parfois davantage : GitHub peut décaler les tâches planifiées).
- **Changer de zone** : modifiez `--bbox LAT_MIN LON_MIN LAT_MAX LON_MAX` dans le workflow.
- **Attribution** : données EUMETSAT (Meteosat Third Generation, Lightning Imager).
- **Test local** : `pip install -r requirements.txt`, définir les deux variables
  d'environnement, puis `python fetch_lightning.py`.
