"""
============================================================================
Middleware Sécurité Industrielle - NIDS Cyber-IA
============================================================================
Implementation des patterns de sécurité industrielle selon OWASP et NIST.
Rate limiting, monitoring, validation, et orchestration microservices.
============================================================================
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from functools import wraps
from collections import defaultdict, deque
import json
import hashlib
import hmac

import redis
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from security_config import get_security_config, validate_environment

# Configuration logging structuré
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("industrial_security")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting pour contexte industriel."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.config = get_security_config()["policies"]["rate_limiting"]
        
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{client_ip}"
        
        # Vérification whitelist
        if client_ip in self.config["whitelist_ips"]:
            return await call_next(request)
            
        # Rate limiting avec Redis
        current_time = int(time.time())
        window_start = current_time - 60  # fenêtre de 1 minute
        
        try:
            # Nettoyage anciennes entrées
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Comptage requêtes actuelles
            current_requests = await self.redis.zcard(key)
            
            if current_requests >= self.config["requests_per_minute"]:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Ajout de la requête actuelle
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, 300)  # TTL 5 minutes
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail-open en cas d'erreur Redis
            
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'IP client avec support pour proxies."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware d'audit et de monitoring de sécurité."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.config = get_security_config()["policies"]["monitoring"]
        
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture des métadonnées de requête
        request_id = self._generate_request_id()
        request.state.request_id = request_id
        
        # Logging de la requête
        await self._log_request(request, request_id)
        
        # Exécution de la requête
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Logging de la réponse
            await self._log_response(request, response, request_id, process_time)
            
            # Vérification des anomalies
            await self._check_anomalies(request, response, process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            await self._log_error(request, e, request_id, process_time)
            raise
    
    def _generate_request_id(self) -> str:
        """Génère un ID unique pour la requête."""
        return hashlib.sha256(
            f"{time.time()}{id(object())}".encode()
        ).hexdigest()[:16]
    
    async def _log_request(self, request: Request, request_id: str):
        """Enregistre les métadonnées de la requête."""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent"),
            "timestamp": time.time()
        }
        
        # Stockage dans Redis pour analyse
        await self.redis.setex(
            f"audit:request:{request_id}",
            86400,  # 24 heures
            json.dumps(log_data)
        )
        
        logger.info(f"Request {request_id}: {request.method} {request.url}")
    
    async def _log_response(self, request: Request, response: Response, 
                          request_id: str, process_time: float):
        """Enregistre les métadonnées de la réponse."""
        log_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": process_time,
            "timestamp": time.time()
        }
        
        await self.redis.setex(
            f"audit:response:{request_id}",
            86400,
            json.dumps(log_data)
        )
        
        logger.info(f"Response {request_id}: {response.status_code} in {process_time:.3f}s")
    
    async def _log_error(self, request: Request, error: Exception, 
                        request_id: str, process_time: float):
        """Enregistre les erreurs."""
        log_data = {
            "request_id": request_id,
            "error": str(error),
            "error_type": type(error).__name__,
            "process_time": process_time,
            "timestamp": time.time()
        }
        
        await self.redis.setex(
            f"audit:error:{request_id}",
            86400,
            json.dumps(log_data)
        )
        
        logger.error(f"Error {request_id}: {error}")
    
    async def _check_anomalies(self, request: Request, response: Response, 
                             process_time: float):
        """Détecte les anomalies de comportement."""
        anomalies = []
        
        # Temps de réponse anormal
        if process_time > 5.0:  # 5 secondes
            anomalies.append("slow_response")
        
        # Codes d'erreur fréquents
        if response.status_code >= 400:
            anomalies.append("error_response")
        
        # Requêtes suspectes
        suspicious_patterns = ["../../../", "..\\..\\", "<script>", "SELECT *"]
        url_lower = str(request.url).lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                anomalies.append("suspicious_pattern")
                break
        
        if anomalies:
            await self._trigger_security_alert(request, anomalies)
    
    async def _trigger_security_alert(self, request: Request, anomalies: List[str]):
        """Déclenche une alerte de sécurité."""
        alert_data = {
            "timestamp": time.time(),
            "anomalies": anomalies,
            "ip": self._get_client_ip(request),
            "url": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("User-Agent")
        }
        
        # Stockage de l'alerte
        await self.redis.lpush(
            "security_alerts",
            json.dumps(alert_data)
        )
        
        # Notification (placeholder pour intégration Slack/Email)
        logger.warning(f"Security alert: {anomalies} from {self._get_client_ip(request)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'IP client."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host

class IndustrialAuthenticator:
    """Système d'authentification industriel avec MFA."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.config = get_security_config()["policies"]["authentication"]
        self.security = HTTPBearer(auto_error=False)
    
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authentifie une requête avec JWT et MFA."""
        credentials = await self.security(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials"
            )
        
        try:
            # Validation JWT
            payload = await self._validate_jwt(credentials.credentials)
            
            # Vérification MFA si requis
            if self.config["require_mfa"]:
                await self._verify_mfa(payload["sub"])
            
            # Vérification blacklist
            if await self._is_blacklisted(payload["sub"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account suspended"
                )
            
            return payload
            
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    async def _validate_jwt(self, token: str) -> Dict[str, Any]:
        """Valide le token JWT."""
        from jose import jwt, JWTError
        
        try:
            config = get_security_config()["jwt"]
            payload = jwt.decode(
                token, 
                config["secret"], 
                algorithms=[config["algorithm"]]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid JWT: {e}")
    
    async def _verify_mfa(self, user_id: str):
        """Vérifie l'authentification multi-facteurs."""
        mfa_key = f"mfa_verified:{user_id}"
        if not await self.redis.exists(mfa_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA verification required"
            )
    
    async def _is_blacklisted(self, user_id: str) -> bool:
        """Vérifie si l'utilisateur est blacklisté."""
        blacklist_key = f"blacklist:{user_id}"
        return await self.redis.exists(blacklist_key)

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Pattern Circuit Breaker pour résilience industrielle."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.config = get_security_config()["microservices"]["service_mesh"]["circuit_breaker"]
        
    async def dispatch(self, request: Request, call_next):
        service_name = self._extract_service_name(request)
        
        # Vérification état du circuit breaker
        if await self._is_circuit_open(service_name):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Service temporarily unavailable"}
            )
        
        try:
            response = await call_next(request)
            await self._record_success(service_name)
            return response
            
        except Exception as e:
            await self._record_failure(service_name)
            raise
    
    def _extract_service_name(self, request: Request) -> str:
        """Extrait le nom du service depuis la requête."""
        path_parts = request.url.path.split("/")
        return path_parts[1] if len(path_parts) > 1 else "unknown"
    
    async def _is_circuit_open(self, service_name: str) -> bool:
        """Vérifie si le circuit breaker est ouvert."""
        state_key = f"circuit_breaker:{service_name}:state"
        state = await self.redis.get(state_key)
        return state == b"open"
    
    async def _record_success(self, service_name: str):
        """Enregistre un succès pour le circuit breaker."""
        failures_key = f"circuit_breaker:{service_name}:failures"
        await self.redis.delete(failures_key)
        await self.redis.set(
            f"circuit_breaker:{service_name}:state", 
            "closed"
        )
    
    async def _record_failure(self, service_name: str):
        """Enregistre un échec pour le circuit breaker."""
        failures_key = f"circuit_breaker:{service_name}:failures"
        failure_count = await self.redis.incr(failures_key)
        
        # Ouverture du circuit après 5 échecs
        if failure_count >= 5:
            await self.redis.setex(
                f"circuit_breaker:{service_name}:state",
                60,  # 1 minute timeout
                "open"
            )
            logger.warning(f"Circuit breaker opened for service: {service_name}")

def create_redis_client() -> redis.Redis:
    """Crée un client Redis avec configuration sécurisée."""
    config = get_security_config()["database"]["redis"]
    
    return redis.Redis(
        host=config["host"],
        port=config["port"],
        password=config["password"],
        ssl=config["ssl"],
        socket_connect_timeout=config["timeout"],
        socket_timeout=config["timeout"],
        retry_on_timeout=True,
        decode_responses=True
    )

# Fonctions utilitaires
def require_auth(authenticator: IndustrialAuthenticator):
    """Décorateur pour exiger l'authentification."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request context not available"
                )
            
            await authenticator.authenticate(request)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_industrial_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valide les données d'entrée pour contexte industriel."""
    rules = get_security_config()["rules"]
    
    # Validation des seuils industriels
    if "connection_rate" in data:
        if data["connection_rate"] > rules["thresholds"]["connection_rate"]:
            raise ValueError("Connection rate exceeds industrial threshold")
    
    if "data_volume" in data:
        if data["data_volume"] > rules["thresholds"]["data_volume"]:
            raise ValueError("Data volume exceeds industrial threshold")
    
    # Nettoyage des données
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Protection contre injection
            sanitized_data[key] = value.replace("<", "&lt;").replace(">", "&gt;")
        else:
            sanitized_data[key] = value
    
    return sanitized_data
