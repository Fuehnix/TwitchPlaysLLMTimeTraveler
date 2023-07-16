# BaseModel is similar to a dataclass (used to store data in a structure way)
from pydantic import BaseModel


class StoryEntry(BaseModel):
    story_action: str = ''
    narration_result: str = ''
    narration_image_url: str = ''


class Proposal(BaseModel):
    user: str
    message: str
    vote: int
