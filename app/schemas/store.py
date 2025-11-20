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
