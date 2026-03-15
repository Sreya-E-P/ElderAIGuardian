"""
Configuration Management with Microsoft Foundry Settings
COMPLETE FIXED VERSION - Includes all database settings
"""

import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from functools import lru_cache
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class Settings(BaseSettings):
    """Application settings loaded from environment and Key Vault"""
    
    # THIS IS THE KEY FIX - allows extra fields from .env without errors
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # This ignores any extra variables in .env not defined here
        case_sensitive=False
    )
    
    # Application
    APP_NAME: str = "Elder AI Guardian"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Microsoft Foundry
    AZURE_FOUNDRY_ENDPOINT: Optional[str] = None
    AZURE_FOUNDRY_PROJECT: str = "elder-ai-guardian"
    AZURE_FOUNDRY_HUB: str = "elder-ai-hub"
    
    # Azure OpenAI (Foundry Deployed)
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    
    # Azure OpenAI Keys (loaded from Key Vault)
    AZURE_OPENAI_KEY: Optional[str] = None
    
    # Azure MCP (Model Context Protocol)
    AZURE_MCP_ENDPOINT: Optional[str] = None
    AZURE_MCP_SERVER: str = "elder-ai-mcp"
    AZURE_MCP_KEY: Optional[str] = None
    
    # Azure Communication
    AZURE_COMMS_CONNECTION_STRING: Optional[str] = None
    AZURE_COMMS_PHONE: Optional[str] = None
    
    # Azure Cosmos DB
    COSMOS_DB_CONNECTION: Optional[str] = None
    COSMOS_DB_DATABASE: str = "elderaidb"
    
    # Azure Storage
    AZURE_STORAGE_CONNECTION: Optional[str] = None
    AZURE_STORAGE_CONTAINER: Optional[str] = "elderai-data"
    AZURE_STORAGE_QUEUE: Optional[str] = "elderai-queue"
    
    # Azure Key Vault
    AZURE_KEYVAULT_URL: Optional[str] = None
    AZURE_KEYVAULT_NAME: Optional[str] = None
    AZURE_KEYVAULT_TENANT_ID: Optional[str] = None
    
    # Azure Monitor
    APPINSIGHTS_CONNECTION_STRING: Optional[str] = None
    APPINSIGHTS_INSTRUMENTATION_KEY: Optional[str] = None
    APPINSIGHTS_SAMPLING_PERCENTAGE: int = 100
    
    # Azure Log Analytics
    LOG_ANALYTICS_WORKSPACE_ID: Optional[str] = None
    LOG_ANALYTICS_KEY: Optional[str] = None
    
    # Azure Search
    AZURE_SEARCH_ENDPOINT: Optional[str] = None
    AZURE_SEARCH_INDEX: Optional[str] = "elderai-index"
    
    # Azure Service Bus
    AZURE_SERVICEBUS_CONNECTION: Optional[str] = None
    
    # Azure Event Grid
    AZURE_EVENTGRID_ENDPOINT: Optional[str] = None
    
    # Azure Subscription
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_RESOURCE_GROUP: Optional[str] = None
    AZURE_LOCATION: str = "eastus"
    
    # Azure AI Project
    AZURE_AI_PROJECT_ENDPOINT: Optional[str] = None
    AZURE_AI_PROJECT_KEY: Optional[str] = None
    AZURE_AI_PROJECT_REGION: str = "eastus"
    
    # Azure Maps
    AZURE_MAPS_KEY: Optional[str] = None
    AZURE_MAPS_CLIENT_ID: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "elderai"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SSL: bool = False
    
    # Database Pool Settings - FIXED: Added these lines
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    
    # MongoDB (optional)
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "elderai"
    
    # Celery (task queue)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_WORKER_CONCURRENCY: int = 4
    
    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    # Elasticsearch
    ELASTICSEARCH_HOSTS: str = "http://localhost:9200"
    ELASTICSEARCH_USER: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    ELASTICSEARCH_INDEX_PREFIX: str = "elderai"
    COSMOS_DB_THROUGHPUT: int = 400
    # JWT Authentication
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth2
    OAUTH2_CLIENT_ID: Optional[str] = None
    OAUTH2_CLIENT_SECRET: Optional[str] = None
    OAUTH2_AUTHORIZATION_URL: Optional[str] = None
    OAUTH2_TOKEN_URL: Optional[str] = None
    
    # External API Keys
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@elderai.com"
    
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    OPENWEATHER_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    # Feature Flags - Microsoft Hero Technologies
    USE_FOUNDRY_SCAM_DETECTION: bool = True
    USE_FOUNDRY_MEDICATION: bool = True
    USE_FOUNDRY_EMERGENCY: bool = True
    USE_MCP_CONTEXT: bool = True
    USE_AGENT_FRAMEWORK: bool = True
    
    # Emergency
    EMERGENCY_SERVICES_PHONE: str = "911"
    PRIMARY_EMERGENCY_CONTACT: Optional[str] = None
    SECONDARY_EMERGENCY_CONTACT: Optional[str] = None
    EMERGENCY_SMS_ENABLED: bool = True
    EMERGENCY_CALL_ENABLED: bool = True
    EMERGENCY_WHATSAPP_ENABLED: bool = True
    
    # Notification Settings
    NOTIFICATION_SMS_ENABLED: bool = True
    NOTIFICATION_EMAIL_ENABLED: bool = True
    NOTIFICATION_PUSH_ENABLED: bool = True
    NOTIFICATION_WHATSAPP_ENABLED: bool = False
    NOTIFICATION_QUIET_HOURS_START: int = 22
    NOTIFICATION_QUIET_HOURS_END: int = 7
    
    # ML Model Thresholds
    PHISHING_THRESHOLD: float = 0.7
    FALL_DETECTION_THRESHOLD: float = 3.0
    ADHERENCE_THRESHOLD: float = 0.6
    PRIORITY_THRESHOLD: float = 0.5
    WELLNESS_THRESHOLD: float = 0.4
    
    # ML Model Paths
    PHISHING_MODEL_PATH: str = "data/models/phishing/model.pkl"
    ADHERENCE_MODEL_PATH: str = "data/models/adherence/model.pkl"
    FALL_DETECTION_MODEL_PATH: str = "data/models/fall_detection/model.pkl"
    PRIORITY_MODEL_PATH: str = "data/models/priority/model.pkl"
    WELLNESS_MODEL_PATH: str = "data/models/wellness/model.pkl"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_OUTPUT: str = "console,file"
    LOG_FILE_PATH: str = "data/logs/elderai.log"
    LOG_MAX_SIZE: str = "100MB"
    LOG_BACKUP_COUNT: int = 10
    
    # Monitoring
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    TRACING_ENABLED: bool = True
    PROFILING_ENABLED: bool = False
    
    # Security
    CORS_ORIGINS: str = "*"
    CORS_CREDENTIALS: bool = True
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: str = ".txt,.pdf,.jpg,.jpeg,.png,.mp3,.wav"
    
    # API Keys (for DevOps)
    DEVOPS_API_KEY: Optional[str] = None
    API_KEY: Optional[str] = None
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_API_URL: str = "http://localhost:8000/api/v1"
    WEBSOCKET_URL: str = "ws://localhost:8000/ws"
    
    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "data/backups"
    BACKUP_AZURE_STORAGE: bool = True
    
    # Development
    DEV_RELOAD: bool = True
    DEV_DEBUG_TOOLBAR: bool = True
    DEV_LOGGING_LEVEL: str = "DEBUG"
    DEV_SKIP_AUTH: bool = False
    DEV_USE_MOCK_SERVICES: bool = True
    
    # Production
    PROD_WORKERS: int = 8
    PROD_MAX_REQUESTS: int = 1000
    PROD_MAX_REQUESTS_JITTER: int = 100
    PROD_GRACEFUL_TIMEOUT: int = 30
    PROD_KEEPALIVE: int = 5
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
    
    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    async def load_from_keyvault(self):
        """Load secrets from Azure Key Vault in production"""
        if self.is_production and self.AZURE_KEYVAULT_URL:
            try:
                credential = DefaultAzureCredential()
                secret_client = SecretClient(
                    vault_url=self.AZURE_KEYVAULT_URL,
                    credential=credential
                )
                
                # Load critical secrets
                secrets = [
                    "AZURE-OPENAI-KEY",
                    "AZURE-COMMS-CONNECTION-STRING",
                    "AZURE-STORAGE-CONNECTION",
                    "AZURE-SERVICEBUS-CONNECTION",
                    "AZURE-FOUNDRY-KEY",
                    "SECRET-KEY",
                    "AZURE-MCP-KEY",
                    "COSMOS-DB-CONNECTION",
                    "AZURE-SEARCH-ENDPOINT"
                ]
                
                for secret_name in secrets:
                    try:
                        secret = secret_client.get_secret(secret_name)
                        env_name = secret_name.replace("-", "_")
                        setattr(self, env_name, secret.value)
                        print(f"✅ Loaded secret: {secret_name}")
                    except Exception as e:
                        print(f"⚠️ Failed to load secret {secret_name}: {e}")
                        
            except Exception as e:
                print(f"❌ Failed to connect to Key Vault: {e}")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()