import asyncio

from .config import vote_delay
from .models import Proposal
from .story_generator import StoryGenerator


class LlmGameHooks:
    async def on_get_narration_result(
        self, narration_result: str, proposal: Proposal, proposal_id: int
    ):
        pass


class LlmGame:
    def __init__(self, hooks: LlmGameHooks = LlmGameHooks()):
        self.generator = StoryGenerator()
        self.background_task = None
        self.hooks = hooks
        self.proposals: list[Proposal] = []
        self.count_votes_event = asyncio.Event()

    @property
    def initial_story_message(self) -> str:
        # We should always have at least the initial story message
        assert self.generator.past_story_entries
        return self.generator.past_story_entries[-1].narration_result

    def vote(self, proposal_id: int, weight: int = 1) -> int:
        if not 0 < proposal_id <= len(self.proposals):
            raise ValueError(f'Invalid proposal id: {proposal_id}')
        self.proposals[proposal_id - 1].vote += weight
        return self.proposals[proposal_id - 1].vote

    def end_vote(self):
        self.count_votes_event.set()

    def restart(self):
        self.generator = StoryGenerator()
        self._new_turn()

    def add_proposal(self, story_action: str, author: str) -> int:
        proposal = Proposal(user=author, message=story_action, vote=0)
        print(proposal)
        self.proposals.append(proposal)
        proposal_id = len(self.proposals)
        if self.background_task is None:
            self.background_task = asyncio.create_task(self._background_thread_run())
        return proposal_id

    async def _background_thread_run(self):
        await asyncio.wait_for(self.count_votes_event.wait(), vote_delay)

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
        self.proposals = []
        self.background_task = None
        self.count_votes_event.clear()
