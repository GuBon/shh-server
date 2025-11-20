from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    DateTime,
    ForeignKey,
    DECIMAL,
    CheckConstraint,
)

from app.core.database import Base


class DistrictCluster(Base):
    """
    상권 클러스터 분석 데이터
    DDL과 정확히 일치하도록 수정
    """
    __tablename__ = "district_clusters"

    # PK - varchar(20)으로 수정
    district_code = Column(String(20), primary_key=True, index=True)
    district_name = Column(String(100), nullable=False)
    
    # 매출 및 고객 분석
    total_revenue = Column(BigInteger, nullable=False)
    total_weighted_age_sum = Column(BigInteger, nullable=False)
    total_foot_traffic = Column(DECIMAL(10, 1), nullable=False)
    business_count = Column(Integer, nullable=False)  # 누락되었던 필드 추가
    avg_age = Column(DECIMAL(8, 5), nullable=False)
    efficiency = Column(DECIMAL(12, 5), nullable=False)

    # 클러스터 분류
    cluster_label = Column(Integer, nullable=False, index=True)
    cluster_type = Column(String(10), nullable=True)  # DDL에서 nullable=True

    # 좌표 정보 (누락되었던 필드들 추가)
    x = Column(DECIMAL(11, 7), nullable=True)  # longitude
    y = Column(DECIMAL(11, 7), nullable=True)  # latitude
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("cluster_label IN (0, 1, 2, 3)", name="chk_cluster_label_dc"),
        CheckConstraint("cluster_type IN ('red', 'orange', 'green', 'blue')", name="chk_cluster_type_dc"),
    )
