from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import UserStore, IndustryCluster
from app.schemas.store import (
    StoreCreate,
    StoreUpdate,
    StoreOut,
    KakaoPlaceBulkRequest,
    KakaoPlaceBulkResponse,
    KakaoPlaceBulkResultItem,
)
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("", response_model=StoreOut)
def create_store(
        data: StoreCreate,
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
):
    store = UserStore(
        user_id=user.id,
        kakao_place_id=data.kakaoPlaceId,
        store_name=data.storeName,
        road_address_name=data.storeAddress,
        # address_name 제거 (유령 필드)
        x=data.longitude,
        y=data.latitude,
        place_url=data.placeUrl,
        phone=data.phone,
        # category_group_name 제거 (유령 필드)
        industry_name=data.industryName,
    )

    cluster = (
        db.query(IndustryCluster)
        .filter(IndustryCluster.industry_name == data.industryName)
        .first()
    )
    if cluster:
        store.industry_cluster_label = cluster.cluster_label
        store.industry_cluster_type = cluster.industry_type_code

    db.add(store)
    db.commit()
    db.refresh(store)

    return StoreOut(
        id=store.id,
        store_name=store.store_name,
        industry_name=store.industry_name,
        district_name=store.district_name,
        # address_name 제거 (유령 필드)
        road_address_name=store.road_address_name,
        x=float(store.x) if store.x is not None else None,
        y=float(store.y) if store.y is not None else None,
    )


@router.patch("/{store_id}", response_model=StoreOut)
def update_store(
        store_id: int,
        data: StoreUpdate,
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
):
    store = db.query(UserStore).filter(UserStore.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="매장을 찾을 수 없습니다.")
    if store.user_id != user.id:
        raise HTTPException(status_code=403, detail="본인 매장만 수정할 수 있습니다.")

    if data.storeName is not None:
        store.store_name = data.storeName
    if data.storeDescription is not None:
        store.store_description = data.storeDescription
    if data.phone is not None:
        store.phone = data.phone
    if data.industryName is not None:
        store.industry_name = data.industryName
        cluster = (
            db.query(IndustryCluster)
            .filter(IndustryCluster.industry_name == data.industryName)
            .first()
        )
        if cluster:
            store.industry_cluster_label = cluster.cluster_label
            store.industry_cluster_type = cluster.industry_type_code

    db.commit()
    db.refresh(store)

    return StoreOut(
        id=store.id,
        store_name=store.store_name,
        industry_name=store.industry_name,
        district_name=store.district_name,
        # address_name 제거 (유령 필드)
        road_address_name=store.road_address_name,
        x=float(store.x) if store.x is not None else None,
        y=float(store.y) if store.y is not None else None,
    )


@router.get("/me/industry")
def get_my_industry(
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
):
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    return {
        "industry_name": store.industry_name,
        "industry_cluster_label": store.industry_cluster_label,
        "industry_cluster_type": store.industry_cluster_type,
    }


@router.get("/me/district")
def get_my_district(
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
):
    """내 상권 정보 조회"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    return {
        "district_code": store.district_code,
        "district_name": store.district_name,
        "district_cluster_label": store.district_cluster_label,
        "district_cluster_type": store.district_cluster_type,
        "coordinates": {
            "latitude": float(store.y) if store.y else None,
            "longitude": float(store.x) if store.x else None
        }
    }


@router.post("/search/kakao/bulk", response_model=KakaoPlaceBulkResponse)
def check_stores_by_place_ids(
        data: KakaoPlaceBulkRequest,
        db: Session = Depends(get_db),
):
    place_ids = [p.placeId for p in data.places]
    if not place_ids:
        return KakaoPlaceBulkResponse(results=[])

    db_stores = (
        db.query(UserStore)
        .filter(UserStore.kakao_place_id.in_(place_ids))
        .all()
    )
    store_map: Dict[str, UserStore] = {s.kakao_place_id: s for s in db_stores}

    results: list[KakaoPlaceBulkResultItem] = []

    for p in data.places:
        store = store_map.get(p.placeId)
        if store:
            results.append(
                KakaoPlaceBulkResultItem(
                    placeId=p.placeId,
                    isMember=True,
                    store=StoreOut(
                        id=store.id,
                        store_name=store.store_name,
                        industry_name=store.industry_name,
                        district_name=store.district_name,
                        # address_name 제거 (유령 필드)
                        road_address_name=store.road_address_name,
                        x=float(store.x) if store.x is not None else None,
                        y=float(store.y) if store.y is not None else None,
                    ),
                )
            )
        else:
            results.append(
                KakaoPlaceBulkResultItem(
                    placeId=p.placeId,
                    isMember=False,
                    store=None,
                )
            )

    return KakaoPlaceBulkResponse(results=results)
