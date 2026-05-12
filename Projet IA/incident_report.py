"""
============================================================================
Rapports d'incidents (LaTeX/PDF) — NIDS Cyber-IA
============================================================================
CdC:
- Génération de rapports automatisés au format LaTeX/PDF (PyLaTeX)
- Contenu: ID incident, horodatage, impact métier, preuves, SHAP, actions

Usage:
  python incident_report.py --json incident.json --out reports/
  python incident_report.py --sample --out reports/
============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Optional

from pylatex import Document, Section, Subsection, Itemize, NoEscape, Command
from pylatex.utils import escape_latex


def _latex_available() -> bool:
    return shutil.which("pdflatex") is not None


def build_report(incident: Dict[str, Any], out_dir: str) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    incident_id = str(incident.get("incident_id") or incident.get("id") or "INC-0001")
    ts = str(incident.get("timestamp") or datetime.now().isoformat())

    verdict = str(incident.get("verdict", "ALLOW"))
    proba = incident.get("attack_probability", None)
    is_anomaly = incident.get("is_anomaly", None)
    top_features = incident.get("top_features", []) or []
    shap_values = incident.get("shap_values", {}) or {}

    impact_metier = str(
        incident.get("business_impact")
        or "Risque d'interruption de visibilité en temps réel / perturbation des flux logistiques."
    )
    actions = incident.get("actions_taken") or [
        "Blocage temporaire de la source (30 min) si confirmé.",
        "Analyse des journaux applicatifs (/auth/login, /deliveries).",
        "Vérification de la dérive de trafic et ajustement du seuil.",
    ]

    doc = Document()
    doc.preamble.append(Command("title", NoEscape(rf"Rapport d'incident — {escape_latex(incident_id)}")))
    doc.preamble.append(Command("date", NoEscape(escape_latex(ts))))
    doc.append(NoEscape(r"\maketitle"))

    with doc.create(Section("Résumé")):
        doc.append(NoEscape(r"\textbf{Verdict:} " + escape_latex(verdict) + NoEscape(r"\\")))
        if proba is not None:
            doc.append(NoEscape(r"\textbf{Probabilité d'attaque:} " + escape_latex(f"{float(proba):.3f}") + NoEscape(r"\\")))
        if is_anomaly is not None:
            doc.append(NoEscape(r"\textbf{Anomalie (auto-encodeur):} " + escape_latex(str(bool(is_anomaly))) + NoEscape(r"\\")))
        doc.append(NoEscape(r"\textbf{Impact métier:} " + escape_latex(impact_metier)))

    with doc.create(Section("Preuves techniques")):
        with doc.create(Subsection("Variables explicatives (Top features)")):
            if top_features:
                with doc.create(Itemize()) as it:
                    for f in top_features[:10]:
                        it.add_item(escape_latex(str(f)))
            else:
                doc.append(escape_latex("Non disponible."))

        with doc.create(Subsection("Valeurs SHAP (échantillon)")):
            if shap_values:
                with doc.create(Itemize()) as it:
                    # top 10 par valeur absolue
                    items = sorted(shap_values.items(), key=lambda kv: abs(float(kv[1])), reverse=True)[:10]
                    for k, v in items:
                        it.add_item(escape_latex(f"{k}: {v}"))
            else:
                doc.append(escape_latex("Non disponible (SHAP désactivé ou modèle non compatible)."))

    with doc.create(Section("Actions et recommandations")):
        with doc.create(Itemize()) as it:
            for a in actions:
                it.add_item(escape_latex(str(a)))

    base_path = os.path.join(out_dir, incident_id.replace("/", "_"))
    tex_path = base_path + ".tex"
    pdf_path = base_path + ".pdf"

    doc.generate_tex(base_path)

    result = {"tex": tex_path}
    if _latex_available():
        # tente la génération PDF via pdflatex
        doc.generate_pdf(base_path, clean_tex=False, compiler="pdflatex")
        if os.path.exists(pdf_path):
            result["pdf"] = pdf_path

    return result


def sample_incident() -> Dict[str, Any]:
    return {
        "incident_id": "INC-2026-0001",
        "timestamp": datetime.now().isoformat(),
        "verdict": "BLOCK",
        "attack_probability": 0.91,
        "is_anomaly": True,
        "top_features": ["sload", "dur", "ct_dst_src_ltm", "sbytes", "sttl"],
        "shap_values": {"sload": 0.42, "dur": -0.21, "ct_dst_src_ltm": 0.19, "sbytes": 0.11, "sttl": 0.05},
        "business_impact": "Risque d'indisponibilité API de suivi de flotte (DoS) et perte de visibilité SCCT.",
        "actions_taken": [
            "Blocage temporaire de l'IP source (30 min).",
            "Inspection des logs de l'API /deliveries sur la période +/- 10 min.",
            "Mise en place d'un rate-limit renforcé sur /auth/login.",
        ],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json", help="Chemin vers un incident JSON")
    p.add_argument("--out", default="reports", help="Dossier de sortie")
    p.add_argument("--sample", action="store_true", help="Génère un rapport à partir d'un incident exemple")
    args = p.parse_args()

    if args.sample:
        incident = sample_incident()
    elif args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            incident = json.load(f)
    else:
        raise SystemExit("Veuillez fournir --json incident.json ou --sample")

    paths = build_report(incident, args.out)
    print("Rapport généré:")
    for k, v in paths.items():
        print(f"- {k}: {v}")
    if "pdf" not in paths:
        print("Note: PDF non généré (pdflatex introuvable). Le .tex est prêt.")


if __name__ == "__main__":
    main()

