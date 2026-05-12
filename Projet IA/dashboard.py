"""
============================================================================
Interface d'Administration (Streamlit) — NIDS Cyber-IA
============================================================================
CdC:
- Dashboard temps réel (score risque, segmentation)
- Agent IA: explications + recommandations
- Workflow: confirmer blocage / ignorer / analyse approfondie
============================================================================
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st


MODULE_B_URL = os.getenv("MODULE_B_URL", "http://127.0.0.1:8000").rstrip("/")
MODULE_A_URL = os.getenv("MODULE_A_URL", "http://127.0.0.1:9000").rstrip("/")


def _agent_ia(security: Dict[str, Any]) -> str:
    verdict = security.get("verdict", "ALLOW")
    proba = float(security.get("attack_probability", 0.0))
    is_anomaly = bool(security.get("is_anomaly", False))
    anomaly_score = security.get("anomaly_score", None)
    top_feats = security.get("top_features", []) or []

    nature = "Trafic normal"
    if verdict == "BLOCK" or proba >= 0.70 or is_anomaly:
        nature = "Suspicion d'intrusion (attaque probable)"
        if is_anomaly and proba < 0.5:
            nature = "Anomalie potentielle (zero-day probable)"

    preuves = []
    if top_feats:
        preuves.append(f"- Variables dominantes: {', '.join(top_feats[:5])}")
    preuves.append(f"- Probabilité d'attaque (stacking): {proba:.3f}")
    preuves.append(f"- Anomalie (auto-encodeur): {is_anomaly}")
    if anomaly_score is not None:
        preuves.append(f"- Score anomalie: {anomaly_score}")

    conseil = []
    if verdict == "BLOCK" or proba >= 0.70 or is_anomaly:
        conseil.append("- Action recommandée: blocage temporaire IP (30 min) + revue logs /auth/login et /deliveries")
        conseil.append("- Vérifier spikes: taux de paquets, durée très courte, charges sload/dload")
    else:
        conseil.append("- Action recommandée: autoriser, surveiller la tendance (baseline) et activer mode bloquant si dérive")

    return "\n".join(
        [
            f"**Nature**: {nature}",
            "",
            "**Preuves techniques**:",
            *preuves,
            "",
            "**Conseil stratégique**:",
            *conseil,
        ]
    )


def _get_json(url: str) -> Dict[str, Any]:
    with httpx.Client(timeout=5.0) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    with httpx.Client(timeout=10.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json()


def _init_state():
    if "events" not in st.session_state:
        st.session_state.events = []  # list[dict]


st.set_page_config(page_title="NIDS Cyber-IA — Admin", layout="wide")
_init_state()

st.title("NIDS Cyber-IA — Dashboard Admin (CdC)")
st.caption(f"Module B: `{MODULE_B_URL}` | Module A: `{MODULE_A_URL}`")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Health Module B"):
        try:
            data = _get_json(f"{MODULE_B_URL}/health")
            st.success(data)
        except Exception as e:
            st.error(str(e))
with col2:
    if st.button("Model info"):
        try:
            data = _get_json(f"{MODULE_B_URL}/model-info")
            st.json(data)
        except Exception as e:
            st.error(str(e))
with col3:
    st.write("")

st.divider()

st.subheader("Test rapide — envoyer un flux au Module B")

default_flow = {
    "dur": 0.001,
    "proto": "tcp",
    "service": "http",
    "state": "FIN",
    "spkts": 5,
    "dpkts": 0,
    "sbytes": 1200,
    "dbytes": 0,
    "rate": 5000,
    "sttl": 254,
    "dttl": 0,
    "sload": 100000,
    "dload": 0,
    "sloss": 0,
    "dloss": 0,
    "sinpkt": 0.01,
    "dinpkt": 0.0,
    "sjit": 0.0,
    "djit": 0.0,
    "swin": 0,
    "stcpb": 0,
    "dtcpb": 0,
    "dwin": 0,
    "tcprtt": 0.0,
    "synack": 0.0,
    "ackdat": 0.0,
    "smean": 240,
    "dmean": 0,
    "trans_depth": 1,
    "response_body_len": 0,
    "ct_srv_src": 1,
    "ct_state_ttl": 1,
    "ct_dst_ltm": 1,
    "ct_src_dport_ltm": 1,
    "ct_dst_sport_ltm": 1,
    "ct_dst_src_ltm": 1,
    "is_ftp_login": 0,
    "ct_ftp_cmd": 0,
    "ct_flw_http_mthd": 1,
    "ct_src_ltm": 1,
    "ct_srv_dst": 1,
    "is_sm_ips_ports": 0,
}

with st.expander("Payload du flux (modifiable)"):
    st.json(default_flow)

if st.button("Analyser (Module B /predict)"):
    try:
        res = _post_json(f"{MODULE_B_URL}/predict", default_flow)
        res["received_at"] = datetime.now().isoformat()
        st.session_state.events.insert(0, res)
        st.success("Analyse reçue")
        st.json(res)
        st.markdown(_agent_ia(res))
    except Exception as e:
        st.error(str(e))

st.divider()

st.subheader("Historique des alertes (session)")

events = st.session_state.events
if not events:
    st.info("Aucune alerte pour l’instant.")
else:
    df = pd.DataFrame(events)
    df["risk"] = df.get("attack_probability", 0.0)
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Événements", len(df))
    with kpi2:
        st.metric("BLOCK", int((df["verdict"] == "BLOCK").sum()))
    with kpi3:
        st.metric("Anomalies", int(df.get("is_anomaly", False).sum()))

    fig = px.histogram(df, x="attack_probability", color="verdict", nbins=20, title="Distribution des probabilités d'attaque")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df[["timestamp", "verdict", "attack_probability", "is_anomaly", "inference_time_ms"]], use_container_width=True)

    st.subheader("Agent IA — analyse du dernier événement")
    st.markdown(_agent_ia(events[0]))

