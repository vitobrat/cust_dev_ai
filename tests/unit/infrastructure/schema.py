from pydantic import BaseModel


class StructuredOutputSchema(BaseModel):
    """Simple schema used to validate structured responses."""

    text: str
