from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import UserStore
from app.api.v1.auth import get_current_user
from app.services.recommendation import recommend_for_industry_db
from app.schemas.recommendation import IndustryRecommendationResponse
from app.services.recommendation import recommend_for_industry_name

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/industries", response_model=IndustryRecommendationResponse)
def recommend_industries_for_me(
        top_n: int = Query(3, ge=1, le=10),
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
):
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    return recommend_for_industry_db(db, store.industry_name, top_n=top_n)

# 로그인 X / 회원 검증 X / 그냥 업종 이름만 넣으면 추천
@router.get(
    "/test-industry",
    response_model=IndustryRecommendationResponse,
    summary="업종 이름으로 유클리드 거리 기반 추천 테스트"
)
def test_recommend_industry(
        industry_name: str = Query(..., description="industry_clusters.industry_name"),
        top_n: int = Query(3, ge=1, le=10),
        db: Session = Depends(get_db)
):
    return recommend_for_industry_name(db, industry_name, top_n)