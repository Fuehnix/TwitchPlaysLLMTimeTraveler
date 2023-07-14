import asyncio

from typing import List

from fastapi import FastAPI

from .llm_game import LlmGame
from .llm_twitch_bot import LlmTwitchBot
from .models import Proposal, StoryEntry


app = FastAPI()

# We need to maintain a reference to running coroutines to prevent GC
background_task = None


@app.on_event('startup')
def on_startup():
    global background_task
    app.state.game = game = LlmGame()
    app.state.bot = bot = LlmTwitchBot(game)
    game.hooks = bot
    background_task = asyncio.create_task(bot.start())


@app.get('/proposals')
def get_proposals() -> List[Proposal]:
    game: LlmGame = app.state.game
    return game.proposals


@app.get('/story-history')
def get_story_history() -> List[StoryEntry]:
    game: LlmGame = app.state.game
    return game.generator.past_story_entries
