from pydantic import BaseModel


class StructuredOutputSchema(BaseModel):
    """Simple schema used to validate structured responses."""

    text: str


class DummyStateSchema(BaseModel):
    """Schema representing the minimal input the base graph expects."""

    input: str


class DummyOutputSchema(BaseModel):
    """Schema representing the base graph output for validation."""

    output: str
