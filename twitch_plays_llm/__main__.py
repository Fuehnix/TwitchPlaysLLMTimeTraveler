import openai

from .config import config
from .llm_game import LlmGame
from .llm_twitch_bot import LlmTwitchBot


def main():
    openai.api_key = config.openai_api_key
    llm_game = LlmGame()
    bot = LlmTwitchBot(llm_game)
    llm_game.hooks = bot
    bot.run()


if __name__ == '__main__':
    main()
