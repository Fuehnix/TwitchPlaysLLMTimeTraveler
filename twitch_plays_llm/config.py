# Load the configuration file
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    twitch_bot_username: str
    twitch_bot_client_id: str
    twitch_channel_name: str
    openai_api_key: str

    vote_delay: int = 20

    model_config = SettingsConfigDict(env_file='.env')


config = Settings()
