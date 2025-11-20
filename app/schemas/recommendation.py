from typing import List

from pydantic import BaseModel


class IndustryRecommendationItem(BaseModel):
    industryName: str
    similarityScore: float
    avgAge: float
    avgFemaleRatio: float
    clusterLabel: int
    comment: str


class IndustryRecommendationResponse(BaseModel):
    userIndustry: str
    clusterLabel: int
    clusterName: str
    recommendations: List[IndustryRecommendationItem]
