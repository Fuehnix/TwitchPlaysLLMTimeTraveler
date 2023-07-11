from argparse import ArgumentParser

import openai

from .config import config
from .llm_game import LlmGame
from .llm_twitch_bot import LlmTwitchBot


def main():
    parser = ArgumentParser(
        description='Backend for Twitch-Plays-LLM, an interactive collaborative text-based twitch game'
    )
    sp = parser.add_subparsers(dest='action')
    sp.add_parser('run')
    args = parser.parse_args()

    if args.action == 'run':
        openai.api_key = config.openai_api_key
        llm_game = LlmGame()
        bot = LlmTwitchBot(llm_game)
        llm_game.hooks = bot
        bot.run()
    else:
        assert False


if __name__ == '__main__':
    main()
