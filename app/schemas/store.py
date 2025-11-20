from typing import Optional, List

from pydantic import BaseModel


class StoreCreate(BaseModel):
    kakaoPlaceId: Optional[str] = None
    storeName: str
    storeAddress: str
    latitude: float
    longitude: float
    placeUrl: Optional[str] = None
    industryName: str
    phone: Optional[str] = None
    # categoryGroupName 제거 (유령 필드)


class StoreUpdate(BaseModel):
    storeName: Optional[str] = None
    storeDescription: Optional[str] = None
    industryName: Optional[str] = None
    phone: Optional[str] = None


# ----- 매장 정보 수정 전용 스키마 -----
class StoreInfoUpdate(BaseModel):
    """매장 정보 수정 (상세 내용만)"""
    storeDescription: Optional[str] = None


class StoreImageUpload(BaseModel):
    """매장 이미지 업로드"""
    imageUrl: str
    sequence: int  # 1~5

    class Config:
        json_schema_extra = {
            "example": {
                "imageUrl": "https://example.com/image.jpg",
                "sequence": 1
            }
        }


class StoreImageOut(BaseModel):
    """매장 이미지 출력"""
    id: int
    imageUrl: str
    sequence: int

    class Config:
        from_attributes = True


class StoreDetailOut(BaseModel):
    """매장 상세 정보 (이미지 포함)"""
    id: int
    store_name: str
    industry_name: str
    district_name: Optional[str]
    road_address_name: Optional[str]
    phone: Optional[str]
    store_description: Optional[str]
    x: Optional[float]
    y: Optional[float]
    images: List[StoreImageOut] = []

    class Config:
        from_attributes = True


class StoreOut(BaseModel):
    id: int
    store_name: str
    industry_name: str
    district_name: Optional[str]
    # address_name 제거 (유령 필드)
    road_address_name: Optional[str]
    x: Optional[float]
    y: Optional[float]

    class Config:
        from_attributes = True


# ----- Kakao 배치 검색 -----
class KakaoPlaceItem(BaseModel):
    placeId: str
    name: Optional[str] = None


class KakaoPlaceBulkRequest(BaseModel):
    places: List[KakaoPlaceItem]


class KakaoPlaceBulkResultItem(BaseModel):
    placeId: str
    isMember: bool
    store: Optional[StoreOut] = None


class KakaoPlaceBulkResponse(BaseModel):
    results: List[KakaoPlaceBulkResultItem]
