import asyncio

from contextlib import suppress
import time
from typing import Optional

from .config import config
from .models import Proposal
from .story_generator import StoryGenerator


class LlmGameHooks:
    """
    Hooks that get called for various events within the game.
    """

    async def on_get_narration_result(
        self, narration_result: str, proposal: Proposal, proposal_id: int
    ):
        """
        Triggered after choosing a proposal and generating a narration result.

        Args:
            narration_result: The generated story narration.
            proposal: The proposal object that led to the narration result.
            proposal_id: The unique id of the proposal.
        """
        pass


class LlmGame:
    """
    Main game logic, handling story generation, proposal management and voting.

    Args:
        hooks: Handlers
    """

    def __init__(self, hooks: LlmGameHooks = LlmGameHooks()):
        self.generator = StoryGenerator()
        self.background_task = None
        self.hooks = hooks
        self.proposals = []
        self.count_votes_event = asyncio.Event()
        self.next_count_vote_time: Optional[int] = None

    @property
    def initial_story_message(self) -> str:
        """
        Returns the initial story message.

        Returns:
            The initial story message.
        """
        assert self.generator.past_story_entries
        return self.generator.past_story_entries[-1].narration_result

    def vote(self, proposal_id: int, weight: int = 1) -> Proposal:
        """
        Adds a vote to a proposal.

        Args:
            proposal_id: The id of the proposal to be voted.
            weight: The weight of the vote (defaults to 1).

        Returns:
            The proposal object that was voted on.
        """
        if not 0 < proposal_id <= len(self.proposals):
            raise ValueError(f'Invalid proposal id: {proposal_id}')
        self.proposals[proposal_id - 1].vote += weight
        return self.proposals[proposal_id - 1]

    def end_vote(self):
        """Ends the voting process by setting the count_votes_event."""
        self.count_votes_event.set()

    def restart(self):
        """Restarts the game by resetting the story generator and initializing a new turn."""
        self.generator = StoryGenerator()
        self._new_turn()

    def add_proposal(self, story_action: str, author: str) -> int:
        """
        Adds a proposal for an action for the main character to take

        Args:
            story_action: The proposed story action by a user.
            author: The username of the person submitting the proposal.

        Returns:
            The id of the newly created proposal.
        """
        proposal = Proposal(user=author, message=story_action, vote=0)
        print(proposal)
        self.proposals.append(proposal)
        proposal_id = len(self.proposals)
        if self.background_task is None:
            self.background_task = asyncio.create_task(self._background_thread_run())
        return proposal_id

    async def _background_thread_run(self):
        """
        A private asynchronous method which handles the collection of
        the votes after the time limit has elapsed
        """
        print('Waiting for votes...')
        self.next_count_vote_time = time.time() + config.vote_delay
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self.count_votes_event.wait(), config.vote_delay)

        self.next_count_vote_time = None
        print('Waiting complete!')

        proposal = max(self.proposals, key=lambda x: x.vote)
        proposal_id = self.proposals.index(proposal)
        narration_result = await self.generator.generate_next_story_narration(
            proposal.message
        )
        await self.hooks.on_get_narration_result(
            narration_result, proposal, proposal_id
        )
        self._new_turn()

    def _new_turn(self):
        """Initializes a new turn within the game"""
        self.proposals = []
        self.background_task = None
        self.count_votes_event.clear()
