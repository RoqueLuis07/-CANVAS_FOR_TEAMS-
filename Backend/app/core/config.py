import logging
import warnings

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "changeme-please-set-a-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Canvas
    canvas_base_url: str = "https://canvas.instructure.com"
    canvas_access_token: str = ""
    canvas_account_id: str = "1"

    # Supabase
    supabase_database_url: str = ""

    # Azure
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_sku_students: str = "STANDARDWOFFPACK_STUDENT"
    azure_sku_teachers: str = "STANDARDWOFFPACK_FACULTY"

    # App
    port: int = 3000
    environment: str = "development"
    site_url: str = "http://localhost:3000"
    secret_key: str = _DEFAULT_SECRET
    auth_cookie_name: str = "usil_auth"

    # Institutional domain & defaults
    institutional_domain: str = "usil.edu.py"
    usage_location: str = "PY"
    teams_url: str = "https://teams.microsoft.com"

    # SMTP (envío de correos de bienvenida/credenciales)
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "it@usil.edu.py"

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_server and self.smtp_user and self.smtp_password)



    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == _DEFAULT_SECRET:
            msg = (
                "SECRET_KEY usa el valor por defecto inseguro. "
                "Establece SECRET_KEY en el archivo .env antes de desplegar en producción."
            )
            warnings.warn(msg, stacklevel=2)
            logger.warning(msg)
        return v

    @property
    def is_insecure_secret(self) -> bool:
        return self.secret_key == _DEFAULT_SECRET


settings = Settings()
