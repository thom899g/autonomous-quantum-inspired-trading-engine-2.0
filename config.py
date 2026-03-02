"""
Configuration management for Autonomous Quantum-Inspired Trading Engine 2.0
Centralizes all system configurations, environment variables, and constants.
Architectural Rationale: Separation of concerns prevents hardcoded values 
and enables runtime configuration changes without code modification.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TradingMode(Enum):
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    private_key_id: Optional[str] = None
    private_key: Optional[str] = None
    client_email: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not self.project_id:
            logging.error("Firebase project_id is required")
            return False
        
        # For local development, credentials can be optional if using ADC
        if self.client_email and not self.private_key:
            logging.error("Firebase private_key required when client_email provided")
            return False
            
        return True

@dataclass
class ExchangeConfig:
    """Exchange API configuration"""
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    sandbox: bool = True
    rate_limit: int = 1000
    
    def get_exchange_id(self) -> str:
        return self.name.lower().replace(" ", "_")

class ConfigManager:
    """Singleton configuration manager with validation"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._initialized = True
    
    def _load_config(self) -> None:
        """Load configuration from environment variables and defaults"""
        try:
            # Core trading settings
            self._config.update({
                "trading_mode": TradingMode(os.getenv("TRADING_MODE", "paper")),
                "base_currency": os.getenv("BASE_CURRENCY", "USDT"),
                "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "1000.0")),
                "risk_per_trade": float(os.getenv("RISK_PER_TRADE", "0.02")),
                "data_timeframe": os.getenv("DATA_TIMEFRAME", "1h"),
                "lookback_period": int(os.getenv("LOOKBACK_PERIOD", "100")),
            })
            
            # Firebase configuration
            firebase_config = FirebaseConfig(
                project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
                private_key_id=os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                private_key=os.getenv("FIREBASE_PRIVATE_KEY"),
                client_email=os.getenv("FIREBASE_CLIENT_EMAIL"),
            )
            
            if not firebase_config.validate():
                self.logger.warning("Firebase configuration incomplete - some features disabled")
            
            self._config["firebase"] = firebase_config
            
            # Exchange configuration
            self._config["exchange"] = ExchangeConfig(
                name=os.getenv("EXCHANGE_NAME", "binance"),
                api_key=os.getenv("EXCHANGE_API_KEY"),
                api_secret=os.getenv("EXCHANGE_API_SECRET"),
                sandbox=os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true",
                rate_limit=int(os.getenv("EXCHANGE_RATE_LIMIT", "1000"))
            )
            
            # Quantum optimization parameters
            self._config.update({
                "qubo_num_qubits": int(os.getenv("QUBO_NUM_QUBITS", "8")),
                "qa_iterations": int(os.getenv("QA_ITERATIONS", "1000")),
                "tunneling_rate": float(os.getenv("TUNNELING_RATE", "0.5")),
                "quantum_annealing_temp": float(os.getenv("QUANTUM_ANNEALING_TEMP", "0.1")),
            })
            
            # Neuro-symbolic parameters
            self._config.update({
                "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.75")),
                "symbolic_weight": float(os.getenv("SYMBOLIC_WEIGHT", "0.3")),
                "neural_weight": float(os.getenv("NEURAL_WEIGHT", "0.7")),
            })
            
            self.logger.info("Configuration loaded successfully")
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Configuration loading failed: {e}")
            raise RuntimeError(f"Invalid configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback"""
        return self._config.get(key, default)
    
    def validate_runtime_config(self) -> bool:
        """Validate all runtime configurations"""
        errors = []
        
        # Check trading mode requirements
        if self._config["trading_mode"] == TradingMode.LIVE:
            if not self._config["exchange"].api_key or not self._config["exchange"].api_secret:
                errors.append("Live trading requires exchange API credentials")
        
        # Validate numeric parameters
        if self._config["risk_per_trade"] <= 0 or self._config["risk_per_trade"] > 0.5:
            errors.append("Risk per trade must be between 0 and 0.5")
        
        if self._config["max_position_size"] <= 0:
            errors.append("Max position size must be positive")
        
        if errors:
            for error in errors:
                self.logger.error(f"Config validation error: {error}")
            return False
            
        return True

# Global configuration instance
config = ConfigManager()