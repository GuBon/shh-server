from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import UserStore, IndustryCluster, StoreImage
from app.schemas.store import (
    StoreCreate,
    StoreUpdate,
    StoreOut,
    StoreInfoUpdate,
    StoreImageUpload,
    StoreImageOut,
    StoreDetailOut,
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


# ----- 새로운 매장 정보 수정 APIs -----

@router.get("/me/detail", response_model=StoreDetailOut)
def get_my_store_detail(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """내 매장 상세 정보 조회 (이미지 포함)"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    # 이미지들도 함께 조회
    images = (
        db.query(StoreImage)
        .filter(StoreImage.user_store_id == store.id)
        .order_by(StoreImage.sequence)
        .all()
    )

    return StoreDetailOut(
        id=store.id,
        store_name=store.store_name,
        industry_name=store.industry_name,
        district_name=store.district_name,
        road_address_name=store.road_address_name,
        phone=store.phone,
        store_description=store.store_description,
        x=float(store.x) if store.x is not None else None,
        y=float(store.y) if store.y is not None else None,
        images=[
            StoreImageOut(
                id=img.id,
                imageUrl=img.image_url,
                sequence=img.sequence
            )
            for img in images
        ]
    )


@router.patch("/me/info", response_model=dict)
def update_my_store_info(
    data: StoreInfoUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """내 매장 상세 내용 수정"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    # 상세 내용 업데이트
    if data.storeDescription is not None:
        store.store_description = data.storeDescription

    db.commit()
    db.refresh(store)

    return {
        "success": True,
        "message": "매장 정보가 성공적으로 수정되었습니다.",
        "updated_data": {
            "store_description": store.store_description
        }
    }


@router.post("/me/images", response_model=StoreImageOut)
def add_store_image(
    data: StoreImageUpload,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """매장 이미지 추가"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    # sequence 유효성 검사
    if not (1 <= data.sequence <= 5):
        raise HTTPException(status_code=400, detail="이미지 순서는 1~5 사이여야 합니다.")

    # 동일한 sequence가 이미 있는지 확인
    existing_image = (
        db.query(StoreImage)
        .filter(
            StoreImage.user_store_id == store.id,
            StoreImage.sequence == data.sequence
        )
        .first()
    )

    if existing_image:
        raise HTTPException(
            status_code=400, 
            detail=f"순서 {data.sequence}에 이미 이미지가 있습니다. 먼저 삭제해주세요."
        )

    # 이미지 추가
    new_image = StoreImage(
        user_store_id=store.id,
        image_url=data.imageUrl,
        sequence=data.sequence
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return StoreImageOut(
        id=new_image.id,
        imageUrl=new_image.image_url,
        sequence=new_image.sequence
    )


@router.get("/me/images", response_model=List[StoreImageOut])
def get_my_store_images(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """내 매장 이미지 목록 조회"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    images = (
        db.query(StoreImage)
        .filter(StoreImage.user_store_id == store.id)
        .order_by(StoreImage.sequence)
        .all()
    )

    return [
        StoreImageOut(
            id=img.id,
            imageUrl=img.image_url,
            sequence=img.sequence
        )
        for img in images
    ]


@router.put("/me/images/{image_id}")
def update_store_image(
    image_id: int,
    data: StoreImageUpload,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """매장 이미지 수정"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    image = (
        db.query(StoreImage)
        .filter(
            StoreImage.id == image_id,
            StoreImage.user_store_id == store.id
        )
        .first()
    )
    
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    # sequence 유효성 검사
    if not (1 <= data.sequence <= 5):
        raise HTTPException(status_code=400, detail="이미지 순서는 1~5 사이여야 합니다.")

    # 다른 이미지가 동일한 sequence를 사용하는지 확인
    if data.sequence != image.sequence:
        existing_image = (
            db.query(StoreImage)
            .filter(
                StoreImage.user_store_id == store.id,
                StoreImage.sequence == data.sequence,
                StoreImage.id != image_id
            )
            .first()
        )

        if existing_image:
            raise HTTPException(
                status_code=400, 
                detail=f"순서 {data.sequence}에 이미 다른 이미지가 있습니다."
            )

    # 이미지 업데이트
    image.image_url = data.imageUrl
    image.sequence = data.sequence

    db.commit()
    db.refresh(image)

    return {
        "success": True,
        "message": "이미지가 성공적으로 수정되었습니다.",
        "updated_image": StoreImageOut(
            id=image.id,
            imageUrl=image.image_url,
            sequence=image.sequence
        )
    }


@router.delete("/me/images/{image_id}")
def delete_store_image(
    image_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """매장 이미지 삭제"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")

    image = (
        db.query(StoreImage)
        .filter(
            StoreImage.id == image_id,
            StoreImage.user_store_id == store.id
        )
        .first()
    )
    
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    db.delete(image)
    db.commit()

    return {
        "success": True,
        "message": "이미지가 성공적으로 삭제되었습니다.",
        "deleted_image_id": image_id
    }
