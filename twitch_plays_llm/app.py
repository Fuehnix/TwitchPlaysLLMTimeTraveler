import asyncio
import time

from typing import List, Optional
import openai

from pydantic import BaseModel
from fastapi import FastAPI

from .llm_game import LlmGame
from .llm_twitch_bot import LlmTwitchBot
from .models import Proposal, StoryEntry
from .story_generator import StoryGenerator
from .config import config


app = FastAPI()

# We need to maintain a reference to running coroutines to prevent GC
background_task = None

from fastapi.middleware.cors import CORSMiddleware


origins = [
    "http://localhost:3000",  # React app is served from this URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class TimeRemainingResponse(BaseModel):
    seconds_remaining: float
    total_seconds: float


@app.get('/vote-time-remaining')
def get_story_history() -> Optional[TimeRemainingResponse]:
    game: LlmGame = app.state.game
    if game.next_count_vote_time is None:
        return None
    return TimeRemainingResponse(
        seconds_remaining=game.next_count_vote_time - time.time(),
        total_seconds=config.vote_delay
    )


@app.post("/generate-image")
async def generate_image():
    generator = StoryGenerator()

    # Generate a description of the current scene
    scene_description = await generator.generate_image_prompt()

    # Send this description to the DALL-E API
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: openai.Image.create(
        prompt=scene_description,
        n=1,
        size="1024x1024"
    ))

    # Return the generated image
    return {"image": response['data'][0]['url']}
