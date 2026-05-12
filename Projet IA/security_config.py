"""
============================================================================
Configuration Sécurité Industrielle - NIDS Cyber-IA
============================================================================
Configuration centralisée de la sécurité pour contexte industriel réel.
Basée sur les meilleures pratiques OWASP et NIST SP 800-162.
============================================================================
"""

import os
import secrets
from typing import Dict, List, Optional

# ──────────────────────────────────────────────────────────────────────────
# Configuration JWT Sécurisée
# ──────────────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(64))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30
JWT_REFRESH_EXPIRATION_DAYS = 7

# ──────────────────────────────────────────────────────────────────────────
# Politiques de Sécurité Industrielle
# ──────────────────────────────────────────────────────────────────────────
SECURITY_POLICIES = {
    "rate_limiting": {
        "enabled": True,
        "requests_per_minute": 100,
        "burst_size": 20,
        "whitelist_ips": ["127.0.0.1", "::1"]
    },
    "authentication": {
        "max_attempts": 5,
        "lockout_duration_minutes": 15,
        "password_min_length": 12,
        "require_mfa": True
    },
    "encryption": {
        "tls_version": "1.3",
        "cipher_suites": ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"],
        "cert_validation": True
    },
    "monitoring": {
        "log_level": "INFO",
        "audit_retention_days": 90,
        "alert_threshold": 0.8,
        "real_time_monitoring": True
    }
}

# ──────────────────────────────────────────────────────────────────────────
# Règles de Détection Industrielles
# ──────────────────────────────────────────────────────────────────────────
INDUSTRIAL_RULES = {
    "critical_protocols": ["modbus", "opc_ua", "dnp3", "iec_61850"],
    "suspicious_patterns": [
        "port_scan", "brute_force", "ddos", "lateral_movement",
        "data_exfiltration", "command_injection", "privilege_escalation"
    ],
    "thresholds": {
        "connection_rate": 1000,  # connexions/seconde
        "data_volume": 1000000000,  # bytes/seconde
        "failed_auth_rate": 10,  # tentatives/seconde
        "anomaly_score": 0.85
    }
}

# ──────────────────────────────────────────────────────────────────────────
# Configuration Microservices (OWASP)
# ──────────────────────────────────────────────────────────────────────────
MICROSERVICES_CONFIG = {
    "service_mesh": {
        "enabled": True,
        "mtls": True,
        "circuit_breaker": True,
        "retry_policy": {
            "max_attempts": 3,
            "backoff_factor": 2,
            "timeout_seconds": 30
        }
    },
    "api_gateway": {
        "edge_authorization": True,
        "service_authorization": True,
        "request_validation": True,
        "response_compression": True
    },
    "service_discovery": {
        "type": "consul",  # ou etcd, kubernetes
        "health_check_interval": 30,
        "deregistration_delay": 60
    }
}

# ──────────────────────────────────────────────────────────────────────────
# Base de données et Cache
# ──────────────────────────────────────────────────────────────────────────
DATABASE_CONFIG = {
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "password": os.getenv("REDIS_PASSWORD"),
        "ssl": True,
        "connection_pool_size": 20,
        "timeout": 5
    },
    "postgresql": {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": "nids_industrial",
        "ssl_mode": "require",
        "connection_pool_size": 25,
        "max_overflow": 10
    }
}

# ──────────────────────────────────────────────────────────────────────────
# Monitoring et Observabilité
# ──────────────────────────────────────────────────────────────────────────
MONITORING_CONFIG = {
    "prometheus": {
        "enabled": True,
        "port": 9090,
        "metrics_path": "/metrics",
        "histogram_buckets": [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
    },
    "grafana": {
        "enabled": True,
        "port": 3000,
        "dashboards": ["nids_overview", "security_metrics", "performance"]
    },
    "elasticsearch": {
        "enabled": True,
        "hosts": ["localhost:9200"],
        "index_pattern": "nids-*",
        "retention_days": 30
    },
    "jaeger": {
        "enabled": True,
        "port": 16686,
        "sampling_rate": 0.1
    }
}

# ──────────────────────────────────────────────────────────────────────────
# Configuration Industrielle Spécifique
# ──────────────────────────────────────────────────────────────────────────
INDUSTRIAL_CONFIG = {
    "scada_systems": {
        "protected_subnets": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
        "critical_assets": ["plc_controllers", "hmi_systems", "historians"],
        "backup_tolerance_minutes": 5
    },
    "compliance": {
        "standards": ["ISO 27001", "IEC 62443", "NIST CSF", "GDPR"],
        "audit_frequency_days": 30,
        "report_recipients": ["security@company.com", "compliance@company.com"]
    },
    "incident_response": {
        "escalation_levels": 3,
        "auto_containment": True,
        "notification_channels": ["email", "slack", "sms"],
        "forensic_preservation": True
    }
}

def get_security_config() -> Dict:
    """Retourne la configuration de sécurité complète."""
    return {
        "jwt": {
            "secret": JWT_SECRET,
            "algorithm": JWT_ALGORITHM,
            "expiration_minutes": JWT_EXPIRATION_MINUTES,
            "refresh_expiration_days": JWT_REFRESH_EXPIRATION_DAYS
        },
        "policies": SECURITY_POLICIES,
        "rules": INDUSTRIAL_RULES,
        "microservices": MICROSERVICES_CONFIG,
        "database": DATABASE_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "industrial": INDUSTRIAL_CONFIG
    }

def validate_environment() -> List[str]:
    """Valide que les variables d'environnement nécessaires sont présentes."""
    required_vars = [
        "JWT_SECRET", "REDIS_HOST", "DB_HOST", 
        "MODULE_B_URL", "MODULE_A_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars
