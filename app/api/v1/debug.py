from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.models.district import DistrictCluster
from app.models.user import IndustryCluster

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/table-structure")
def check_table_structure(db: Session = Depends(get_db)):
    """테이블 구조 확인"""
    try:
        # industry_clusters 테이블 구조 확인
        result = db.execute(text('DESCRIBE industry_clusters;'))
        columns = result.fetchall()
        
        table_structure = []
        for col in columns:
            field, type_, null, key, default, extra = col[:6] if len(col) >= 6 else col + [None] * (6 - len(col))
            table_structure.append({
                "field": field,
                "type": type_,
                "null": null,
                "key": key,
                "default": default,
                "extra": extra
            })
        
        # 샘플 데이터도 확인
        result = db.execute(text('SELECT * FROM industry_clusters LIMIT 3;'))
        rows = result.fetchall()
        
        sample_data = []
        if rows:
            result = db.execute(text('SELECT * FROM industry_clusters LIMIT 0;'))
            column_names = list(result.keys())
            
            for row in rows:
                sample_data.append(dict(zip(column_names, row)))
        
        return {
            "table_structure": table_structure,
            "sample_data": sample_data
        }
        
    except Exception as e:
        return {"error": str(e)}


@router.get("/district-clusters")
def get_district_clusters_sample(db: Session = Depends(get_db)):
    """district_clusters 테이블 샘플 데이터 조회"""
    
    # 전체 개수
    total_count = db.query(DistrictCluster).count()
    
    # 좌표가 있는 개수
    with_coordinates = db.query(DistrictCluster).filter(
        DistrictCluster.x.isnot(None),
        DistrictCluster.y.isnot(None)
    ).count()
    
    # 샘플 5개
    samples = (
        db.query(DistrictCluster)
        .limit(5)
        .all()
    )
    
    return {
        "total_count": total_count,
        "with_coordinates": with_coordinates,
        "samples": [
            {
                "district_code": d.district_code,
                "district_name": d.district_name,
                "x": float(d.x) if d.x else None,
                "y": float(d.y) if d.y else None,
                "cluster_type": d.cluster_type
            }
            for d in samples
        ]
    }


@router.get("/industry-clusters")
def get_industry_clusters_sample(db: Session = Depends(get_db)):
    """industry_clusters 테이블 샘플 데이터 조회"""
    
    # 전체 개수
    total_count = db.query(IndustryCluster).count()
    
    # 샘플 10개
    samples = (
        db.query(IndustryCluster)
        .limit(10)
        .all()
    )
    
    return {
        "total_count": total_count,
        "samples": [
            {
                "industry_name": i.industry_name,
                "cluster_label": i.cluster_label,
                "industry_type_code": i.industry_type_code
            }
            for i in samples
        ]
    }


@router.get("/search-industry/{industry_name}")
def search_industry(industry_name: str, db: Session = Depends(get_db)):
    """특정 업종 검색"""
    
    # 정확한 매칭
    exact_match = (
        db.query(IndustryCluster)
        .filter(IndustryCluster.industry_name == industry_name)
        .first()
    )
    
    # 부분 매칭
    partial_matches = (
        db.query(IndustryCluster)
        .filter(IndustryCluster.industry_name.like(f"%{industry_name}%"))
        .limit(5)
        .all()
    )
    
    return {
        "search_term": industry_name,
        "exact_match": {
            "industry_name": exact_match.industry_name,
            "cluster_label": exact_match.cluster_label,
            "industry_type_code": exact_match.industry_type_code
        } if exact_match else None,
        "partial_matches": [
            {
                "industry_name": i.industry_name,
                "cluster_label": i.cluster_label,
                "industry_type_code": i.industry_type_code
            }
            for i in partial_matches
        ]
    }


@router.get("/test-coordinates")
def test_coordinates(x: float, y: float, db: Session = Depends(get_db)):
    """좌표 기반 가장 가까운 상권 찾기 테스트"""
    
    from app.services.district_service import DistrictService
    
    result = DistrictService.find_nearest_district_cluster(db, x, y)
    
    return {
        "input_coordinates": {"x": x, "y": y},
        "nearest_district": result
    }
