from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.models.user import User, UserStore, IndustryCluster
from app.schemas.auth import SignupRequest, UserOut, Token
from app.services.district_service import DistrictService

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/check-username")
def check_username(login_id: str, db: Session = Depends(get_db)):
    """아이디 중복 체크"""
    exists = db.query(User).filter(User.login_id == login_id).first()
    return {
        "available": exists is None,
        "message": None if exists is None else "이미 사용 중인 아이디입니다.",
    }


@router.post("/verify-business")
def verify_business(businessNumber: str):
    digits = "".join(ch for ch in businessNumber if ch.isdigit())
    if len(digits) != 10:
        raise HTTPException(status_code=400, detail="올바른 사업자등록번호를 입력해주세요.")

    # 실제에선 외부 API 연동. 지금은 Mock.
    return {
        "success": True,
        "verified": True,
        "businessInfo": {
            "businessName": "소확행 샘플 상호",
            "representativeName": "홍길동",
            "businessType": "일반과세자",
            "businessStatus": "영업중",
        },
    }


@router.post("/signup", response_model=UserOut)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    try:
        # 1. 중복 아이디 체크
        if db.query(User).filter(User.login_id == data.login_id).first():
            raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

        # 2. 사용자 생성
        user = User(
            login_id=data.login_id,
            password=hash_password(data.password),
            name=data.name,
        )
        db.add(user)
        db.flush()  # commit 대신 flush로 변경 (ID 생성하지만 트랜잭션 유지)
        
        print(f"✅ User created with ID: {user.id}")

        # 3. 🎯 매장 좌표로 가장 가까운 상권 찾기
        store_info = data.store_info
        print(f"📍 Finding nearest district for coordinates: x={store_info.x}, y={store_info.y}")
        
        nearest_district = DistrictService.find_nearest_district_cluster(
            db, store_info.x, store_info.y  # x=경도, y=위도
        )
        print(f"🏢 Nearest district: {nearest_district}")

        # 4. 업종 클러스터 정보 조회
        print(f"🏭 Looking up industry cluster for: {store_info.industry_name}")
        industry_cluster = DistrictService.get_industry_cluster_info(
            db, store_info.industry_name
        )
        print(f"📊 Industry cluster: {industry_cluster}")

        # 5. 매장 정보 저장 (에러 방지를 위해 기본값 설정)
        print("🏪 Creating user store...")
        user_store = UserStore(
            user_id=user.id,
            kakao_place_id=store_info.kakao_place_id,
            store_name=store_info.store_name,
            place_url=store_info.place_url,
            phone=store_info.phone,
            road_address_name=store_info.road_address_name,
            # address_name 제거 (유령 필드)
            industry_name=store_info.industry_name,
            x=store_info.x,
            y=store_info.y,
            # 기본값 설정 (에러 방지)
            district_code=None,
            district_name=None, 
            district_cluster_label=None,
            district_cluster_type=None,
            industry_cluster_label=None,
            industry_cluster_type=None,
        )

        # 6. 상권 정보 매핑 (가장 가까운 상권이 있는 경우)
        if nearest_district:
            user_store.district_code = nearest_district["district_code"]
            user_store.district_name = nearest_district["district_name"]
            user_store.district_cluster_label = nearest_district["district_cluster_label"]
            user_store.district_cluster_type = nearest_district["district_cluster_type"]
            print(f"✅ District info mapped: {nearest_district['district_code']}")

        # 7. 업종 클러스터 정보 매핑 (업종 정보가 있는 경우)
        if industry_cluster:
            user_store.industry_cluster_label = industry_cluster["industry_cluster_label"]
            user_store.industry_cluster_type = industry_cluster["industry_cluster_type"]
            print(f"✅ Industry cluster mapped: {industry_cluster}")

        print("💾 Adding user_store to session...")
        db.add(user_store)
        
        print("💾 Committing transaction...")
        db.commit()
        
        print("✅ Signup completed successfully!")
        return UserOut(id=user.id, loginId=user.login_id, name=user.name)
        
    except Exception as e:
        print(f"❌ Error during signup: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        db.rollback()  # 에러 발생시 롤백
        raise HTTPException(status_code=500, detail=f"회원가입 중 오류가 발생했습니다: {str(e)}")


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login_id == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
