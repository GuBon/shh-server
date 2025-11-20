from pydantic import BaseModel


class SignupStoreInfo(BaseModel):
    kakao_place_id: str = None
    store_name: str
    place_url: str = None 
    phone: str = None
    road_address_name: str
    industry_name: str
    x: float  # longitude (경도)
    y: float  # latitude (위도)


class SignupRequest(BaseModel):
    login_id: str  # userId -> login_id로 변경
    password: str
    name: str
    store_info: SignupStoreInfo
    # business_number 제거 (실제로 사용하지 않음)


class UserOut(BaseModel):
    id: int
    loginId: str
    name: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
