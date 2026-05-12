# NIDS Cyber‑IA (UNSW‑NB15) — Projet complet (CdC)

Ce dépôt implémente le cahier des charges **NIDS Cyber‑IA** avec une architecture **découplée Sidecar** :

- **Module A (Interface Métier Logistique)**: `module_a.py` (FastAPI)
- **Module B (Security Engine)**: `main.py` (FastAPI) + `train_model.py` + `preprocess.py`
- **Dashboard Admin + “Agent IA”**: `dashboard.py` (Streamlit)
- **Rapport incident (LaTeX/PDF)**: `incident_report.py` (PyLaTeX)

## Démarrage rapide (Windows / PowerShell)

Créer l’environnement et installer les dépendances :

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.runtime.txt
```

> Si tu veux aussi **entraîner** les modèles (TensorFlow, SHAP, LightGBM, XGBoost…), installe ensuite:
>
> ```bash
> pip install -r requirements.txt
> ```

### Lancer tout en 1 clic (scripts Windows)

```bash
.\scripts\run_all.ps1
```

Arrêt (kill ports 8000/9000/8501) :

```bash
.\scripts\stop_ports.ps1
```

### Lancer tout via Docker Compose

Construire et démarrer :

```bash
docker compose up --build
```

Ports :
- Module B (Security Engine): `http://127.0.0.1:8000/docs`
- Module A (API métier): `http://127.0.0.1:9000/docs`
- Dashboard: `http://127.0.0.1:8501`

### 1) Entraîner les modèles (Module B)

```bash
python train_model.py
```

Cela crée les artefacts dans `models/` (stacking, auto‑encodeur, scaler, encoders, etc.).

### 2) Lancer le Module B (Security Engine)

```bash
python -m uvicorn main:app --reload --port 8000
```

Test :

- `GET` `http://127.0.0.1:8000/health`
- `POST` `http://127.0.0.1:8000/predict`

### 3) Lancer le Module A (API métier)

```bash
python -m uvicorn module_a:app --reload --port 9000
```

Login démo :

- `POST /auth/login` avec `{"username":"admin","password":"admin"}`
- Le JWT retourné sert ensuite pour appeler `/deliveries` et `/stocks` (header `Authorization: Bearer <token>`).

### 4) Lancer le dashboard

```bash
streamlit run dashboard.py
```

## Rapports d’incidents (TeX/PDF)

Générer un rapport exemple :

```bash
python incident_report.py --sample --out reports
```

Si `pdflatex` n’est pas installé, le script génère quand même le `.tex`.

## Notes CdC (alignement)

- **Découplage**: Module A envoie des métadonnées au Module B (sidecar). Par défaut, le traitement métier reste **non‑bloquant** sauf sur opérations sensibles (ex: `/auth/login`).
- **ML**: Stacking (LightGBM/XGBoost/RF + LR) + Auto‑encodeur (anomalies/zero‑day), SMOTE train‑only, RFE 20 features.
- **XAI**: SHAP calculé côté Module B et affichable dans l’UI (top features).

## Simulation d’attaque (démo)

Quand les services tournent:

```bash
python attack_sim.py --target module_b --n 200 --concurrency 20
python attack_sim.py --target module_a_login --n 80 --concurrency 10
```

