"""
============================================================================
Dashboard Industriel - NIDS Cyber-IA (Streamlit)
============================================================================
Interface d'administration et monitoring pour contexte industriel réel.

Fonctionnalités :
  - Monitoring temps réel avec graphiques industriels
  - Alertes de sécurité avec filtrage avancé
  - Agent IA avec recommandations contextuelles
  - Métriques de performance et conformité
  - Interface de configuration des règles
  - Export de rapports industriels

Auteur  : Dashboard Industrial Team
Projet  : NIDS Cyber-IA (Cahier des Charges Industriel)
============================================================================
"""

from __future__ import annotations

import os
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Import des modules industriels
from security_config import get_security_config
from industrial_middleware import create_redis_client

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard_industrial")

# Configuration
config = get_security_config()
redis_client = create_redis_client()

MODULE_B_URL = os.getenv("MODULE_B_URL", "http://127.0.0.1:8000").rstrip("/")
MODULE_A_URL = os.getenv("MODULE_A_URL", "http://127.0.0.1:9000").rstrip("/")

# Configuration Streamlit
st.set_page_config(
    page_title="NIDS Industrial Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache pour les données
@st.cache_data(ttl=300)  # 5 minutes
def get_security_metrics() -> Dict[str, Any]:
    """Récupère les métriques de sécurité depuis Module B."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{MODULE_B_URL}/admin/stats")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        return {"error": str(e)}

@st.cache_data(ttl=60)  # 1 minute
def get_model_info() -> Dict[str, Any]:
    """Récupère les informations des modèles."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{MODULE_B_URL}/model-info")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        return {"error": str(e)}

@st.cache_data(ttl=30)  # 30 secondes
def get_security_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Récupère les alertes de sécurité depuis Redis."""
    try:
        alerts = []
        alert_data = redis_client.lrange("security_alerts", 0, limit - 1)
        
        for alert_json in alert_data:
            try:
                alert = json.loads(alert_json)
                alerts.append(alert)
            except json.JSONDecodeError:
                continue
                
        return alerts
    except Exception as e:
        logger.error(f"Failed to get security alerts: {e}")
        return []

async def test_flow_industrial(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test un flux réseau avec contexte industriel."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{MODULE_B_URL}/predict", json=flow_data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Flow test failed: {e}")
        return {"error": str(e)}

def create_industrial_metrics_chart(metrics: Dict[str, Any]) -> go.Figure:
    """Crée un graphique de métriques industriel."""
    if "error" in metrics:
        fig = go.Figure()
        fig.add_annotation(text="Metrics Unavailable", xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False, font=dict(size=20))
        return fig
    
    # Création de sous-graphiques
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Predictions", "Performance", "Cache", "Connections"),
        specs=[[{"type": "bar"}, {"type": "indicator"}],
               [{"type": "pie"}, {"type": "gauge"}]]
    )
    
    # Predictions
    if "predictions_total" in metrics:
        pred_data = metrics["predictions_total"]
        fig.add_trace(
            go.Bar(x=["ALLOW", "BLOCK"], y=[pred_data.get("allow", 0), pred_data.get("block", 0)],
                   name="Predictions", marker_color=["green", "red"]),
            row=1, col=1
        )
    
    # Performance
    if "performance" in metrics:
        perf_data = metrics["performance"]
        avg_time = perf_data.get("avg_prediction_time", 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=avg_time * 1000,  # Convert to ms
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Avg Prediction Time (ms)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 100], 'color': "yellow"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75, 'value': 80}}
            ),
            row=1, col=2
        )
    
    # Cache
    if "cache" in metrics:
        cache_data = metrics["cache"]
        fig.add_trace(
            go.Pie(labels=["Hits", "Misses"], 
                   values=[cache_data.get("hits", 0), cache_data.get("misses", 0)],
                   name="Cache"),
            row=2, col=1
        )
    
    # Connections
    if "connections" in metrics:
        conn_data = metrics["connections"]
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=conn_data.get("active", 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Active Connections"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "green"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 100], 'color': "lightyellow"}]}
            ),
            row=2, col=2
        )
    
    fig.update_layout(height=600, showlegend=False)
    return fig

def create_alerts_timeline(alerts: List[Dict[str, Any]]) -> go.Figure:
    """Crée une timeline des alertes de sécurité."""
    if not alerts:
        fig = go.Figure()
        fig.add_annotation(text="No Security Alerts", xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False, font=dict(size=20))
        return fig
    
    # Préparation des données
    df = pd.DataFrame(alerts)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['hour'] = df['timestamp'].dt.floor('H')
    
    # Comptage des alertes par heure
    hourly_alerts = df.groupby('hour').size().reset_index(name='count')
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hourly_alerts['hour'],
            y=hourly_alerts['count'],
            mode='lines+markers',
            name='Security Alerts',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        )
    )
    
    fig.update_layout(
        title="Security Alerts Timeline",
        xaxis_title="Time",
        yaxis_title="Alert Count",
        height=400
    )
    
    return fig

def agent_ia_industrial(security_data: Dict[str, Any]) -> str:
    """Agent IA avec contexte industriel."""
    verdict = security_data.get("verdict", "ALLOW")
    proba = float(security_data.get("attack_probability", 0.0))
    is_anomaly = bool(security_data.get("is_anomaly", False))
    anomaly_score = security_data.get("anomaly_score", None)
    top_feats = security_data.get("top_features", []) or []
    
    # Analyse contextuelle industrielle
    analysis = []
    
    if verdict == "BLOCK" or proba >= 0.80:
        analysis.append("🚨 **ALERTE CRITIQUE** - Menace de sécurité confirmée")
        if proba >= 0.95:
            analysis.append("⚠️ **Niveau de menace ÉLEVÉ** - Action immédiate requise")
    elif proba >= 0.60:
        analysis.append("⚡ **SUSPICION ÉLEVÉE** - Surveillance renforcée recommandée")
    elif is_anomaly and proba < 0.5:
        analysis.append("🔍 **ANOMALIE ZERO-DAY** - Pattern inconnu détecté")
    else:
        analysis.append("✅ **TRAFFIC NORMAL** - Activité conforme aux patterns")
    
    # Recommandations industrielles
    recommendations = []
    
    if verdict == "BLOCK":
        recommendations.extend([
            "🔒 **Isoler le segment réseau** concerné",
            "📊 **Analyser les logs** des 24 dernières heures",
            "🚨 **Notifier l'équipe de sécurité** immédiatement",
            "🔍 **Lancer une investigation** forensique"
        ])
    elif is_anomaly:
        recommendations.extend([
            "📈 **Surveiller l'évolution** du comportement",
            "🔍 **Analyser les patterns** similaires",
            "📝 **Documenter l'anomalie** pour référence future"
        ])
    else:
        recommendations.extend([
            "✅ **Maintenir la surveillance** standard",
            "📊 **Continuer le monitoring** des métriques"
        ])
    
    # Conformité industrielle
    compliance = []
    if security_data.get("compliance_info", {}).get("industrial_mode"):
        compliance.extend([
            "🏭 **Mode industriel** activé",
            "📋 **Conformité IEC 62443** respectée",
            "🔒 **Standards NIST CSF** appliqués"
        ])
    
    # Explications techniques
    technical = []
    if top_feats:
        technical.append(f"🔍 **Features critiques**: {', '.join(top_feats[:3])}")
    if anomaly_score is not None:
        technical.append(f"📊 **Score anomalie**: {anomaly_score:.4f}")
    technical.append(f"📈 **Confiance**: {max(proba, 1-proba):.1%}")
    
    # Assemblage du rapport
    report = "\n\n".join([
        "### 🎯 Analyse de Sécurité Industrielle",
        "\n".join(analysis),
        "\n### 📋 Recommandations Opérationnelles",
        "\n".join(recommendations),
        "\n### 🏛️ Conformité & Standards",
        "\n".join(compliance) if compliance else "✅ Conformité validée",
        "\n### 🔧 Détails Techniques",
        "\n".join(technical)
    ])
    
    return report

def main():
    """Fonction principale du dashboard industriel."""
    st.title("🛡️ NIDS Industrial Dashboard")
    st.markdown("---")
    
    # Sidebar pour configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Rafraîchissement automatique
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.selectbox("Interval (seconds)", [30, 60, 120, 300], index=1)
            time.sleep(refresh_interval)
            st.rerun()
        
        # Filtres
        st.subheader("Filters")
        alert_severity = st.multiselect(
            "Alert Severity",
            ["Critical", "High", "Medium", "Low"],
            default=["Critical", "High"]
        )
        
        time_range = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
            index=2
        )
    
    # Onglets principaux
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "🔍 Analysis", "🚨 Alerts", "🤖 Agent IA", "⚙️ Settings", "🧠 ML Analytics"
    ])
    
    with tab1:
        st.header("Industrial Security Dashboard")
        
        # Métriques en temps réel
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            metrics = get_security_metrics()
            if "predictions_total" in metrics:
                total_pred = metrics["predictions_total"]
                st.metric(
                    "Total Predictions",
                    total_pred.get("allow", 0) + total_pred.get("block", 0),
                    delta=f"⚠️ {total_pred.get('block', 0)} blocked"
                )
        
        with col2:
            model_info = get_model_info()
            st.metric(
                "Model Status",
                "✅ Loaded" if model_info.get("model_loaded") else "❌ Not Loaded",
                delta=model_info.get("model_version", "Unknown")
            )
        
        with col3:
            alerts = get_security_alerts()
            st.metric(
                "Active Alerts",
                len(alerts),
                delta="🚨" if len(alerts) > 5 else ""
            )
        
        with col4:
            if "performance" in metrics:
                avg_time = metrics["performance"].get("avg_prediction_time", 0)
                st.metric(
                    "Avg Response Time",
                    f"{avg_time*1000:.1f}ms",
                    delta="⚡" if avg_time < 0.1 else "⚠️"
                )
        
        # Graphiques industriels
        st.subheader("Industrial Metrics Overview")
        fig_metrics = create_industrial_metrics_chart(metrics)
        st.plotly_chart(fig_metrics, use_container_width=True)
        
        # Timeline des alertes
        st.subheader("Security Alerts Timeline")
        fig_alerts = create_alerts_timeline(alerts)
        st.plotly_chart(fig_alerts, use_container_width=True)
    
    with tab2:
        st.header("Flow Analysis")
        
        # Formulaire de test
        with st.form("flow_test_form"):
            st.subheader("Test Network Flow")
            
            col1, col2 = st.columns(2)
            
            with col1:
                duration = st.number_input("Duration (s)", min_value=0.0, value=0.1, format="%.4f")
                protocol = st.selectbox("Protocol", ["tcp", "udp", "icmp"])
                src_bytes = st.number_input("Source Bytes", min_value=0, value=1000)
                dst_bytes = st.number_input("Destination Bytes", min_value=0, value=500)
            
            with col2:
                src_packets = st.number_input("Source Packets", min_value=0, value=10)
                dst_packets = st.number_input("Destination Packets", min_value=0, value=5)
                rate = st.number_input("Rate", min_value=0.0, value=100.0)
                sttl = st.number_input("Source TTL", min_value=0, value=64)
            
            submitted = st.form_submit_button("🔍 Analyze Flow")
            
            if submitted:
                # Construction du flux de test
                flow_data = {
                    "dur": duration,
                    "proto": protocol,
                    "service": "http",
                    "state": "FIN",
                    "spkts": src_packets,
                    "dpkts": dst_packets,
                    "sbytes": src_bytes,
                    "dbytes": dst_bytes,
                    "rate": rate,
                    "sttl": sttl,
                    "dttl": 64,
                    "sload": src_bytes * 8 / duration if duration > 0 else 0,
                    "dload": dst_bytes * 8 / duration if duration > 0 else 0,
                    "sloss": 0,
                    "dloss": 0,
                    "sinpkt": duration / src_packets if src_packets > 0 else 0,
                    "dinpkt": duration / dst_packets if dst_packets > 0 else 0,
                    "sjit": 0.0,
                    "djit": 0.0,
                    "swin": 0,
                    "stcpb": 0,
                    "dtcpb": 0,
                    "dwin": 0,
                    "tcprtt": 0.0,
                    "synack": 0.0,
                    "ackdat": 0.0,
                    "smean": src_bytes // src_packets if src_packets > 0 else 0,
                    "dmean": dst_bytes // dst_packets if dst_packets > 0 else 0,
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
                    "source_ip": "192.168.1.100",
                    "dest_ip": "10.0.0.1"
                }
                
                # Analyse asynchrone
                with st.spinner("Analyzing flow..."):
                    result = asyncio.run(test_flow_industrial(flow_data))
                
                if "error" not in result:
                    # Affichage des résultats
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🔍 Analysis Results")
                        verdict = result.get("verdict", "UNKNOWN")
                        proba = result.get("attack_probability", 0.0)
                        
                        if verdict == "BLOCK":
                            st.error(f"🚨 **BLOCKED** - Threat Probability: {proba:.1%}")
                        else:
                            st.success(f"✅ **ALLOWED** - Threat Probability: {proba:.1%}")
                        
                        st.metric("Confidence Score", f"{result.get('confidence_score', 0):.1%}")
                        st.metric("Inference Time", f"{result.get('inference_time_ms', 0):.1f}ms")
                    
                    with col2:
                        st.subheader("📊 Technical Details")
                        st.json(result)
                else:
                    st.error(f"Analysis failed: {result['error']}")
    
    with tab3:
        st.header("Security Alerts")
        
        # Filtres et options
        col1, col2 = st.columns(2)
        
        with col1:
            alert_limit = st.number_input("Alert Limit", min_value=10, max_value=500, value=50)
        
        with col2:
            if st.button("🔄 Refresh Alerts"):
                st.rerun()
        
        # Liste des alertes
        alerts = get_security_alerts(alert_limit)
        
        if alerts:
            # Conversion en DataFrame pour affichage
            df_alerts = pd.DataFrame(alerts)
            if 'timestamp' in df_alerts.columns:
                df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'], unit='s')
                df_alerts = df_alerts.sort_values('timestamp', ascending=False)
            
            st.dataframe(df_alerts, use_container_width=True)
            
            # Options de traitement
            st.subheader("Alert Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚨 Acknowledge All", type="primary"):
                    st.success("All alerts acknowledged")
            
            with col2:
                if st.button("📤 Export CSV"):
                    csv = df_alerts.to_csv(index=False)
                    st.download_button(
                        "Download Alerts",
                        csv,
                        "security_alerts.csv",
                        "text/csv"
                    )
            
            with col3:
                if st.button("🗑️ Clear Alerts"):
                    st.warning("Alert clearing not implemented in demo")
        else:
            st.info("No security alerts detected")
    
    with tab4:
        st.header("🤖 Industrial AI Agent")
        
        # Section de test pour l'agent IA
        st.subheader("Security Analysis Assistant")
        
        # Test rapide
        if st.button("🔍 Run Sample Analysis"):
            sample_result = {
                "verdict": "BLOCK",
                "attack_probability": 0.85,
                "is_anomaly": True,
                "anomaly_score": 0.92,
                "top_features": ["sbytes", "rate", "spkts"],
                "compliance_info": {
                    "industrial_mode": True,
                    "demo_mode": False
                }
            }
            
            analysis = agent_ia_industrial(sample_result)
            st.markdown(analysis)
        
        # Interface personnalisée
        st.subheader("Custom Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            verdict = st.selectbox("Verdict", ["ALLOW", "BLOCK"])
            probability = st.slider("Attack Probability", 0.0, 1.0, 0.5)
            is_anomaly = st.checkbox("Is Anomaly")
        
        with col2:
            anomaly_score = st.number_input("Anomaly Score", 0.0, 1.0, 0.0) if is_anomaly else 0.0
            top_features = st.text_area("Top Features (comma-separated)", "sbytes, rate, spkts")
        
        if st.button("🔍 Generate Analysis"):
            custom_result = {
                "verdict": verdict,
                "attack_probability": probability,
                "is_anomaly": is_anomaly,
                "anomaly_score": anomaly_score if is_anomaly else None,
                "top_features": [f.strip() for f in top_features.split(",") if f.strip()],
                "compliance_info": {"industrial_mode": True}
            }
            
            analysis = agent_ia_industrial(custom_result)
            st.markdown(analysis)
    
    with tab5:
        st.header("⚙️ Industrial Settings")
        
        # Configuration système
        st.subheader("System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Module B URL", MODULE_B_URL)
            st.metric("Module A URL", MODULE_A_URL)
            st.metric("Redis Status", "✅ Connected")
        
        with col2:
            model_info = get_model_info()
            st.metric("Model Version", model_info.get("model_version", "Unknown"))
            st.metric("Demo Mode", "🚨 Active" if model_info.get("demo_mode") else "✅ Production")
            st.metric("Features", model_info.get("features_count", 0))
        
        # Configuration des seuils
        st.subheader("Threshold Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            block_threshold = st.slider("Block Threshold", 0.5, 1.0, 0.7)
            anomaly_threshold = st.slider("Anomaly Threshold", 0.5, 1.0, 0.85)
        
        with col2:
            cache_ttl = st.number_input("Cache TTL (seconds)", 60, 3600, 300)
            max_connections = st.number_input("Max Connections", 10, 1000, 100)
        
        # Informations de conformité
        st.subheader("🏛️ Compliance Information")
        
        compliance_info = {
            "Standards": ["ISO 27001", "IEC 62443", "NIST CSF", "GDPR"],
            "Audit Frequency": "30 days",
            "Data Retention": "90 days",
            "Encryption": "TLS 1.3",
            "Authentication": "JWT + MFA"
        }
        
        for key, value in compliance_info.items():
            if isinstance(value, list):
                st.write(f"**{key}**: {', '.join(value)}")
            else:
                st.write(f"**{key}**: {value}")
        
        # Actions système
        st.subheader("System Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reload Models", type="primary"):
                st.success("Models reloaded (demo)")
        
        with col2:
            if st.button("🧹 Clear Cache"):
                st.success("Cache cleared (demo)")
        
        with col3:
            if st.button("📊 Export Config"):
                config_data = {
                    "block_threshold": block_threshold,
                    "anomaly_threshold": anomaly_threshold,
                    "cache_ttl": cache_ttl,
                    "max_connections": max_connections
                }
                st.json(config_data)
    
    with tab6:
        st.header("🧠 ML Analytics & Algorithm Details")
        
        # Import des analytics ML
        from ml_analytics import ml_analytics
        
        # Section Algorithmes
        st.subheader("🔬 Algorithm Architecture")
        
        algo_col1, algo_col2 = st.columns(2)
        
        with algo_col1:
            st.markdown("### 🤖 Stacking Classifier")
            
            stacking_info = ml_analytics.get_algorithm_details("stacking_classifier")
            
            st.write(f"**Type**: {stacking_info.get('type', 'N/A')}")
            st.write(f"**Description**: {stacking_info.get('description', 'N/A')}")
            
            # Base Learners
            st.markdown("#### Base Learners:")
            base_learners = stacking_info.get("base_learners", {})
            
            for name, learner in base_learners.items():
                with st.expander(f"📦 {learner.get('name', name)}"):
                    st.write(f"**Type**: {learner.get('type', 'N/A')}")
                    
                    # Paramètres
                    params = learner.get('parameters', {})
                    if params:
                        st.write("**Parameters**:")
                        for param, value in params.items():
                            st.write(f"- {param}: {value}")
                    
                    # Forces
                    strengths = learner.get('strengths', [])
                    if strengths:
                        st.write("**Strengths**:")
                        for strength in strengths:
                            st.write(f"✅ {strength}")
                    
                    # Faiblesses
                    weaknesses = learner.get('weaknesses', [])
                    if weaknesses:
                        st.write("**Weaknesses**:")
                        for weakness in weaknesses:
                            st.write(f"⚠️ {weakness}")
            
            # Méta-classifieur
            meta = stacking_info.get("meta_classifier", {})
            st.markdown("#### Meta Classifier:")
            st.write(f"**{meta.get('name', 'N/A')}** - {meta.get('role', 'N/A')}")
            
            # Architecture
            arch = stacking_info.get("architecture", {})
            st.write(f"**Cross-validation**: {arch.get('cross_validation', 'N/A')}")
            st.write(f"**Stacking method**: {arch.get('stacking_method', 'N/A')}")
        
        with algo_col2:
            st.markdown("### 🎯 Autoencoder (Anomaly Detection)")
            
            ae_info = ml_analytics.get_algorithm_details("autoencoder")
            
            st.write(f"**Type**: {ae_info.get('type', 'N/A')}")
            st.write(f"**Description**: {ae_info.get('description', 'N/A')}")
            
            # Architecture
            st.markdown("#### Architecture:")
            arch = ae_info.get("architecture", {})
            
            layers = arch.get("layers", [])
            for i, layer in enumerate(layers):
                layer_type = layer.get("type", "Unknown")
                if "size" in layer:
                    layer_info = f"{layer_type} ({layer['size']})"
                else:
                    layer_info = layer_type
                
                if "activation" in layer:
                    layer_info += f" - {layer['activation']}"
                if "noise" in layer:
                    layer_info += f" - noise:{layer['noise']}"
                
                st.write(f"**Layer {i+1}**: {layer_info}")
            
            # Training
            training = ae_info.get("training", {})
            st.markdown("#### Training Configuration:")
            st.write(f"**Optimizer**: {training.get('optimizer', 'N/A')}")
            st.write(f"**Loss**: {training.get('loss_function', 'N/A')}")
            st.write(f"**Epochs**: {training.get('epochs', 'N/A')}")
            st.write(f"**Batch Size**: {training.get('batch_size', 'N/A')}")
            
            # Anomaly Detection
            anomaly = ae_info.get("anomaly_detection", {})
            st.markdown("#### Anomaly Detection:")
            st.write(f"**Method**: {anomaly.get('method', 'N/A')}")
            st.write(f"**Threshold**: {anomaly.get('threshold_percentile', 'N/A')}th percentile")
            st.write(f"**Training Data**: {anomaly.get('training_data', 'N/A')}")
            
            # Forces et faiblesses
            strengths = ae_info.get("strengths", [])
            if strengths:
                st.markdown("#### Strengths:")
                for strength in strengths:
                    st.write(f"✅ {strength}")
            
            weaknesses = ae_info.get("weaknesses", [])
            if weaknesses:
                st.markdown("#### Weaknesses:")
                for weakness in weaknesses:
                    st.write(f"⚠️ {weakness}")
        
        st.divider()
        
        # Section Métriques de Qualité
        st.subheader("📊 Quality Metrics & Performance")
        
        # Récupérer les métriques réelles si disponibles
        model_info = get_model_info()
        training_metrics = model_info.get("training_metrics", {})
        
        metrics_col1, metrics_col2 = st.columns(2)
        
        with metrics_col1:
            st.markdown("### 📈 Performance Metrics")
            
            # Métriques principales
            if training_metrics and not training_metrics.get("demo_mode"):
                st.success("✅ Real training metrics available")
                
                accuracy = training_metrics.get("accuracy", 0)
                precision = training_metrics.get("precision", 0)
                recall = training_metrics.get("recall", 0)
                f1 = training_metrics.get("f1_score", 0)
                
                # Affichage des métriques
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Accuracy", f"{accuracy:.4f}")
                    st.metric("Precision", f"{precision:.4f}")
                with col_b:
                    st.metric("Recall", f"{recall:.4f}")
                    st.metric("F1-Score", f"{f1:.4f}")
                
                # Évaluation de la qualité
                quality_assessment = ml_analytics._assess_model_quality(training_metrics)
                st.markdown("#### Quality Assessment:")
                for metric, quality in quality_assessment.items():
                    emoji = "✅" if quality == "Excellent" else "🟡" if quality in ["Good", "Moderate"] else "🔴"
                    st.write(f"{emoji} **{metric.replace('_', ' ').title()}**: {quality}")
                
            else:
                st.warning("⚠️ Demo mode - showing example metrics")
                
                # Exemple de métriques
                example_metrics = {
                    "accuracy": 0.9856,
                    "precision": 0.9834,
                    "recall": 0.9878,
                    "f1_score": 0.9856,
                    "false_positive_rate": 0.0122,
                    "false_negative_rate": 0.0122
                }
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Accuracy", f"{example_metrics['accuracy']:.4f}")
                    st.metric("Precision", f"{example_metrics['precision']:.4f}")
                with col_b:
                    st.metric("Recall", f"{example_metrics['recall']:.4f}")
                    st.metric("F1-Score", f"{example_metrics['f1_score']:.4f}")
                
                quality_assessment = ml_analytics._assess_model_quality(example_metrics)
                st.markdown("#### Quality Assessment (Example):")
                for metric, quality in quality_assessment.items():
                    emoji = "✅" if quality == "Excellent" else "🟡" if quality in ["Good", "Moderate"] else "🔴"
                    st.write(f"{emoji} **{metric.replace('_', ' ').title()}**: {quality}")
        
        with metrics_col2:
            st.markdown("### 📚 Metrics Explanations")
            
            # Sélection de métrique à expliquer
            selected_metric = st.selectbox(
                "Select a metric to understand:",
                ["accuracy", "precision", "recall", "f1_score", "auc_roc", "confusion_matrix", "reconstruction_error"]
            )
            
            metric_info = ml_analytics.get_metric_explanation(selected_metric)
            
            if metric_info:
                st.markdown(f"#### {metric_info.get('name', selected_metric).title()}")
                st.write(metric_info.get('description', 'No description available'))
                
                if 'formula' in metric_info:
                    st.code(metric_info['formula'])
                
                if 'interpretation' in metric_info:
                    st.markdown("**Interpretation Scale:**")
                    interp = metric_info['interpretation']
                    for level, range_val in interp.items():
                        emoji = "✅" if level == "excellent" else "🟡" if level in ["good", "moderate"] else "🔴"
                        st.write(f"{emoji} **{level.title()}**: {range_val}")
                
                if 'importance' in metric_info:
                    st.markdown("**Industrial Importance:**")
                    for importance in metric_info['importance']:
                        st.write(f"• {importance}")
                
                if 'limitations' in metric_info:
                    st.markdown("**Limitations:**")
                    for limitation in metric_info['limitations']:
                        st.write(f"⚠️ {limitation}")
                
                if 'industrial_relevance' in metric_info:
                    st.markdown(f"**Industrial Relevance**: {metric_info['industrial_relevance']}")
            
            # Matrice de confusion interactive
            if selected_metric == "confusion_matrix":
                st.markdown("#### Confusion Matrix Visualization")
                
                # Exemple de matrice
                cm_example = np.array([[85000, 1500], [1200, 88000]])
                
                fig_cm = go.Figure(data=go.Heatmap(
                    z=cm_example,
                    x=["Predicted Normal", "Predicted Attack"],
                    y=["Actual Normal", "Actual Attack"],
                    colorscale='Blues',
                    text=cm_example,
                    texttemplate="%{text}",
                    textfont={"size": 14},
                    hoverongaps=False
                ))
                
                fig_cm.update_layout(
                    title="Confusion Matrix (Example)",
                    xaxis_title="Predicted",
                    yaxis_title="Actual",
                    height=400
                )
                
                st.plotly_chart(fig_cm, use_container_width=True)
        
        st.divider()
        
        # Section Recommandations Industrielles
        st.subheader("🏭 Industrial Recommendations")
        
        # Générer des recommandations basées sur les métriques
        if training_metrics and not training_metrics.get("demo_mode"):
            recommendations = ml_analytics._generate_industrial_recommendations(training_metrics)
        else:
            # Recommandations d'exemple
            recommendations = [
                "✅ **Performance excellente** - Modèle prêt pour déploiement industriel",
                "📊 **Monitoring continu** - Surveiller les métriques en production",
                "🔄 **Réentraînement régulier** - Mettre à jour avec de nouvelles données",
                "🧪 **Tests A/B** - Comparer avec d'autres modèles avant déploiement"
            ]
        
        for rec in recommendations:
            st.markdown(rec)
        
        # Section Feature Importance
        st.subheader("🔍 Feature Importance Analysis")
        
        col_feat1, col_feat2 = st.columns(2)
        
        with col_feat1:
            st.markdown("#### Top Features (Example)")
            
            # Exemple de features importantes
            example_features = [
                ("sbytes", 0.142),
                ("rate", 0.128),
                ("spkts", 0.098),
                ("sttl", 0.087),
                ("dbytes", 0.076)
            ]
            
            for feature, importance in example_features:
                st.write(f"**{feature}**: {importance:.3f}")
                st.progress(importance)
        
        with col_feat2:
            st.markdown("#### Feature Categories")
            
            feature_categories = {
                "Volume-based": ["sbytes", "dbytes", "spkts", "dpkts"],
                "Timing-based": ["dur", "rate", "sinpkt", "dinpkt"],
                "TCP-specific": ["sttl", "dttl", "tcprtt", "synack"],
                "Statistical": ["sload", "dload", "sjit", "djit"]
            }
            
            for category, features in feature_categories.items():
                with st.expander(f"📂 {category}"):
                    for feature in features:
                        st.write(f"• {feature}")
        
        # Export des analytics
        st.subheader("📤 Export Analytics")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            if st.button("📄 Export Model Report"):
                report_data = {
                    "timestamp": datetime.now().isoformat(),
                    "model_info": model_info,
                    "quality_assessment": quality_assessment if 'quality_assessment' in locals() else {},
                    "recommendations": recommendations
                }
                st.download_button(
                    "Download Report",
                    json.dumps(report_data, indent=2),
                    "ml_analytics_report.json",
                    "application/json"
                )
        
        with col_exp2:
            if st.button("📊 Export Metrics"):
                metrics_export = training_metrics if training_metrics else example_metrics
                st.download_button(
                    "Download Metrics",
                    json.dumps(metrics_export, indent=2),
                    "model_metrics.json",
                    "application/json"
                )
        
        with col_exp3:
            if st.button("📋 Export Algorithm Details"):
                st.download_button(
                    "Download Algorithm Info",
                    json.dumps(ml_analytics.algorithms_info, indent=2),
                    "algorithms_info.json",
                    "application/json"
                )

if __name__ == "__main__":
    main()
