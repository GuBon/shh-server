from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from app.core.database import get_db
from app.models.user import UserStore, IndustryCluster
from app.models.district import DistrictCluster
from app.api.v1.auth import get_current_user
from app.services.district_service import DistrictService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/my-district")
def get_my_district_analysis(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """내 상권 상세 분석"""
    store = db.query(UserStore).filter(UserStore.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="등록된 매장이 없습니다.")
    
    if not store.district_code:
        raise HTTPException(status_code=404, detail="상권 정보가 없습니다.")
    
    # 상권 정보 조회
    district_info = DistrictService.get_district_info(db, store.district_code)
    
    # 업종 정보 조회
    industry_info = DistrictService.get_industry_cluster_info(db, store.industry_name)
    
    # 같은 상권 내 매장 수
    same_district_stores = (
        db.query(UserStore)
        .filter(UserStore.district_code == store.district_code)
        .count()
    )
    
    # 같은 업종 매장 수
    same_industry_stores = (
        db.query(UserStore)
        .filter(
            UserStore.district_code == store.district_code,
            UserStore.industry_name == store.industry_name
        )
        .count()
    )
    
    return {
        "my_store": {
            "store_name": store.store_name,
            "industry_name": store.industry_name,
            "address": store.road_address_name,  # address_name 제거 (유령 필드)
            "coordinates": {
                "latitude": float(store.y) if store.y else None,
                "longitude": float(store.x) if store.x else None
            }
        },
        "district_analysis": district_info,
        "industry_analysis": industry_info,
        "market_position": {
            "stores_in_district": same_district_stores,
            "same_industry_in_district": same_industry_stores,
            "market_share": round(same_industry_stores / max(same_district_stores, 1) * 100, 2)
        }
    }


@router.get("/clusters/{cluster_type}")
def get_cluster_analysis(
    cluster_type: str,
    db: Session = Depends(get_db)
):
    """클러스터별 상권 분석"""
    
    if cluster_type not in ["red", "orange", "green", "blue"]:
        raise HTTPException(status_code=400, detail="유효하지 않은 클러스터 타입입니다.")
    
    # 클러스터 타입을 라벨로 변환
    type_to_label = {"red": 0, "orange": 1, "green": 2, "blue": 3}
    cluster_label = type_to_label[cluster_type]
    
    # 해당 클러스터의 상권들 조회
    districts = (
        db.query(DistrictCluster)
        .filter(DistrictCluster.cluster_label == cluster_label)
        .order_by(DistrictCluster.total_revenue.desc())
        .limit(20)
        .all()
    )
    
    if not districts:
        raise HTTPException(status_code=404, detail="해당 클러스터 데이터를 찾을 수 없습니다.")
    
    # 클러스터 설명
    cluster_descriptions = {
        0: {"name": "☕️ 2030 여성 타겟 상권", "description": "카페, 뷰티 등 젊은 여성층 중심 상권"},
        1: {"name": "🍺 4050 남성 타겟 상권", "description": "주점, 식당 등 중년 남성층 중심 상권"},
        2: {"name": "🛍️ 4050 여성 타겟 상권", "description": "쇼핑, 생활편의 등 중년 여성층 중심 상권"},
        3: {"name": "🎮 2030 남성 타겟 상권", "description": "PC방, 오락 등 젊은 남성층 중심 상권"},
    }
    
    # 통계 계산
    total_revenue = sum(d.total_revenue for d in districts)
    avg_age = sum(d.avg_age for d in districts) / len(districts) if districts else 0
    avg_efficiency = sum(d.efficiency for d in districts) / len(districts) if districts else 0
    
    return {
        "cluster_info": cluster_descriptions[cluster_label],
        "cluster_type": cluster_type,
        "statistics": {
            "total_districts": len(districts),
            "total_revenue": int(total_revenue),
            "avg_age": round(float(avg_age), 2),
            "avg_efficiency": round(float(avg_efficiency), 2)
        },
        "top_districts": [
            {
                "district_code": d.district_code,
                "district_name": d.district_name,
                "total_revenue": int(d.total_revenue),
                "avg_age": float(d.avg_age),
                "efficiency": float(d.efficiency),
                "business_count": d.business_count
            }
            for d in districts[:10]  # 상위 10개만
        ]
    }


@router.get("/districts/nearby")
def get_nearby_districts(
    latitude: float = Query(..., description="위도"),
    longitude: float = Query(..., description="경도"),
    radius: int = Query(2000, description="검색 반경(미터)"),
    db: Session = Depends(get_db)
):
    """주변 상권 분석 - district_clusters 테이블만 사용"""
    
    from sqlalchemy import text
    
    # district_clusters 테이블의 x, y 좌표를 사용하여 거리 계산
    query = text("""
        SELECT 
            dc.district_code,
            dc.district_name,
            dc.x as longitude,
            dc.y as latitude,
            dc.cluster_label,
            dc.cluster_type,
            dc.total_revenue,
            dc.avg_age,
            dc.efficiency,
            dc.business_count,
            (6371000 * acos(
                cos(radians(:lat)) * cos(radians(dc.y)) * 
                cos(radians(dc.x) - radians(:lng)) + 
                sin(radians(:lat)) * sin(radians(dc.y))
            )) as distance_meters
        FROM district_clusters dc
        WHERE dc.x IS NOT NULL AND dc.y IS NOT NULL
        AND (6371000 * acos(
            cos(radians(:lat)) * cos(radians(dc.y)) * 
            cos(radians(dc.x) - radians(:lng)) + 
            sin(radians(:lat)) * sin(radians(dc.y))
        )) <= :radius
        ORDER BY distance_meters ASC
        LIMIT 50
    """)
    
    result = db.execute(query, {
        "lat": latitude,
        "lng": longitude,
        "radius": radius
    })
    
    districts = result.fetchall()
    
    if not districts:
        return {
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_meters": radius,
            "districts": [],
            "summary": {
                "total_count": 0,
                "cluster_distribution": {}
            }
        }
    
    # 클러스터별 분포 계산
    cluster_distribution = {}
    for district in districts:
        cluster_type = district.cluster_type
        if cluster_type:
            cluster_distribution[cluster_type] = cluster_distribution.get(cluster_type, 0) + 1
    
    return {
        "center": {"latitude": latitude, "longitude": longitude},
        "radius_meters": radius,
        "districts": [
            {
                "district_code": d.district_code,
                "district_name": d.district_name,
                "coordinates": {
                    "latitude": float(d.latitude) if d.latitude else None,
                    "longitude": float(d.longitude) if d.longitude else None
                },
                "distance_meters": int(d.distance_meters),
                "cluster_info": {
                    "cluster_label": d.cluster_label,
                    "cluster_type": d.cluster_type,
                    "total_revenue": int(d.total_revenue) if d.total_revenue else None,
                    "avg_age": float(d.avg_age) if d.avg_age else None,
                    "efficiency": float(d.efficiency) if d.efficiency else None,
                    "business_count": d.business_count
                }
            }
            for d in districts
        ],
        "summary": {
            "total_count": len(districts),
            "cluster_distribution": cluster_distribution
        }
    }
