from pydantic import BaseModel, ConfigDict, Field, field_validator


class Question(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=1000)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=1, max_length=2000)

    @field_validator('options')
    @classmethod
    def distinct_options(cls, values):
        if any(not value.strip() for value in values) or len(set(v.strip().casefold() for v in values)) != 4:
            raise ValueError('Answer options must be nonempty and distinct')
        return values


class Quiz(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    questions: list[Question] = Field(min_length=1, max_length=15)

    research: dict | None = None
