from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ib_host: str = '127.0.0.1'
    ib_port: int = 4002
    ib_client_id: int = 1
    ib_readonly: bool = False
    model_config = SettingsConfigDict(extra='allow')

settings = Settings()