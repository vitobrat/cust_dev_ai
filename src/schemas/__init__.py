from src.schemas.interview import (
    InterviewEntitySchema,
    InterviewRelEntitySchema,
)
from src.schemas.persona import PersonaEntitySchema, PersonaRelEntitySchema
from src.schemas.sub_interview import (
    SubInterviewEntitySchema,
    SubInterviewRelEntitySchema,
)
from src.schemas.task import TaskEntitySchema, TaskRelEntitySchema
from src.schemas.user import UserEntitySchema, UserRelEntitySchema

models = [
    UserEntitySchema,
    UserRelEntitySchema,
    InterviewEntitySchema,
    InterviewRelEntitySchema,
    PersonaEntitySchema,
    PersonaRelEntitySchema,
    TaskEntitySchema,
    TaskRelEntitySchema,
    SubInterviewEntitySchema,
    SubInterviewRelEntitySchema,
]

for model in models:  # noqa: WPS481
    model.model_rebuild()
