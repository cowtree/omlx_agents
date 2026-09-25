from typing import Literal

from pydantic import BaseModel, ValidationError, Field

class ArticalAnalysis(BaseModel):
    title: str = Field(
                        description="The title of the article")
    summary: str = Field(
                        description="A brief summary of the article",
                        min_length = 10,
                        max_length = 500
    )
    sentiment: Literal[
                        "positive", 
                        "negative", 
                        "neutral"
                    ] = Field(
                        description="The overall sentiment of the article"
                    )
    confidence: float = Field(
                        description="Confidence score of the sentiment analysis",
                        ge=0.0,
                        le=1.0 
    )


class EntityExtraction(BaseModel):

    people: list[str] = Field(
                        description="List of people mentioned in the article"
    )
    organizations: list[str] = Field(
                        description="List of organizations mentioned in the article"
    )
    locations: list[str] = Field(
                        description="List of locations mentioned in the article"
    )

class PatientExtraction(BaseModel):
    age: int = Field(
                        description="The age of the patient",
                        ge=0
    )
    gender: Literal[
                        "male", 
                        "female", 
                        "other"
                    ] = Field(
                        description="The gender of the patient"
                    )
    diagnosis: str = Field(
                        description="The diagnosis of the patient",
                        min_length = 5,
                        max_length = 200
    )

class CodeReview(BaseModel):
    bugs: list[str]
    severity: Literal[
                        "low",
                        "medium",
                        "high"
                    ]
    
