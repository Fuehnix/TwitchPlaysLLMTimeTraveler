from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    twitch_bot_username: str
    twitch_bot_client_id: str
    twitch_channel_name: str
    openai_api_key: str

    vote_delay: int = 40
    vote_points: int = 100  # points give per vote for all users
    action_cost: int = 100 # points required per action for all users
    vote_accumulation: int = 20 # points per voting round for all users
    points_earned_per_vote: int = 100 # points earned per vote for the user who is voted for
    backend_port: int = 9511

    model_config = SettingsConfigDict(env_file='.env')


config = Settings()
