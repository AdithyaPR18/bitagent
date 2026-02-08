from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    lnd_rest_host: str = "https://localhost:8080"
    lnd_macaroon_path: str = ""
    lnd_tls_cert_path: str = ""
    openai_api_key: str = ""
    stacks_api_url: str = "http://localhost:3999"
    use_mock_lightning: bool = True
    use_mock_llm: bool = True

    macaroon_secret_key: str = "bitagent-hackathon-secret-key-2026"
    base_price_sats: int = 10
    agent_initial_balance: int = 10000
    agent_budget_per_hour: int = 500

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
