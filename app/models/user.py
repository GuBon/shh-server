from datetime import datetime

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    DECIMAL,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    ERD: users - DDL과 100% 일치
    """
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    login_id = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    stores = relationship("UserStore", back_populates="user")


class UserStore(Base):
    """
    ERD: user_stores - DDL과 100% 일치
    """
    __tablename__ = "user_stores"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    kakao_place_id = Column(String(50), nullable=True)
    store_name = Column(String(150), nullable=False)
    place_url = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    road_address_name = Column(String(255), nullable=True)
    industry_name = Column(String(100), nullable=True)
    
    # 좌표 정보 - DDL과 정확히 일치 (11,7)
    x = Column(DECIMAL(11, 7), nullable=True)  # longitude
    y = Column(DECIMAL(11, 7), nullable=True)  # latitude

    # 상권 정보
    district_code = Column(String(20), nullable=True)
    district_name = Column(String(100), nullable=True)
    district_cluster_label = Column(Integer, nullable=True)
    district_cluster_type = Column(String(10), nullable=True)

    # 업종 클러스터 정보
    industry_cluster_label = Column(Integer, nullable=True)
    industry_cluster_type = Column(String(10), nullable=True)

    store_description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    user = relationship("User", back_populates="stores")
    partnerships = relationship("Partnership", back_populates="user_store", cascade="all, delete-orphan")
    images = relationship("StoreImage", back_populates="user_store", cascade="all, delete-orphan")


class IndustryCluster(Base):
    """
    ERD: industry_clusters - DDL과 100% 일치
    """
    __tablename__ = "industry_clusters"

    industry_name = Column(String(100), primary_key=True, index=True, nullable=False)
    avg_age_score = Column(DECIMAL(8, 5), nullable=False)
    avg_female_ratio = Column(DECIMAL(8, 5), nullable=False)
    data_count = Column(Integer, nullable=False)
    cluster_label = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    industry_type_code = Column(String(10), nullable=True)

    __table_args__ = (
        CheckConstraint("cluster_label IN (0, 1, 2, 3)", name="chk_cluster_label_ic"),
    )


class DistrictIndustryMix(Base):
    """
    상권별 업종 분포 데이터 - DDL과 100% 일치
    """
    __tablename__ = "district_industry_mix"

    id = Column(BigInteger, primary_key=True, index=True)
    industry_name = Column(String(100), ForeignKey("industry_clusters.industry_name", ondelete="CASCADE"), nullable=False)
    
    # 각 클러스터별 업종 비율 - DDL과 정확히 일치
    cluster_0_ratio = Column(DECIMAL(10, 8), nullable=True, default=0.00000000)
    cluster_1_ratio = Column(DECIMAL(10, 8), nullable=True, default=0.00000000) 
    cluster_2_ratio = Column(DECIMAL(10, 8), nullable=True, default=0.00000000)
    cluster_3_ratio = Column(DECIMAL(10, 8), nullable=True, default=0.00000000)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 설정
    industry_cluster = relationship("IndustryCluster")


class Partnership(Base):
    """
    제휴 관계 데이터 - DDL과 100% 일치
    """
    __tablename__ = "partnerships"

    id = Column(BigInteger, primary_key=True, index=True)
    user_store_id = Column(BigInteger, ForeignKey("user_stores.id", ondelete="CASCADE"), nullable=False)
    partner_store_name = Column(String(150), nullable=False)
    detail = Column(Text, nullable=True)
    count = Column(Integer, nullable=True, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 설정
    user_store = relationship("UserStore", back_populates="partnerships")


class StoreImage(Base):
    """
    매장 이미지 데이터 - DDL과 100% 일치
    """
    __tablename__ = "store_images"

    id = Column(BigInteger, primary_key=True, index=True)
    user_store_id = Column(BigInteger, ForeignKey("user_stores.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(255), nullable=False)
    sequence = Column(Integer, nullable=False)  # DDL: tinyint -> Integer 호환
    
    # 관계 설정  
    user_store = relationship("UserStore", back_populates="images")

    __table_args__ = (
        CheckConstraint("sequence BETWEEN 1 AND 5", name="chk_sequence_range"),
    )
