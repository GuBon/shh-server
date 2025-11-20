import math
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.district import DistrictCluster
from app.models.user import IndustryCluster


class DistrictService:
    """상권 매핑 및 분석 서비스"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        두 좌표 간의 거리를 계산 (Haversine formula)
        결과는 미터 단위
        """
        R = 6371000  # 지구 반지름 (미터)
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def find_nearest_district_cluster(
        db: Session, 
        store_x: float,  # 매장 경도
        store_y: float   # 매장 위도
    ) -> Optional[Dict]:
        """
        매장 좌표에서 가장 가까운 상권 클러스터 찾기
        district_clusters 테이블의 x, y 좌표와 비교
        
        Returns:
            Dict with district info or None
        """
        try:
            print(f"🔍 Looking for nearest district to store at: x={store_x}, y={store_y}")
            
            # district_clusters 테이블에서 모든 상권 조회
            district_clusters = (
                db.query(DistrictCluster)
                .filter(DistrictCluster.x.isnot(None))
                .filter(DistrictCluster.y.isnot(None))
                .all()
            )
            
            print(f"📊 Found {len(district_clusters)} districts with coordinates")
            
            if not district_clusters:
                print("⚠️  No district clusters found with coordinates")
                return None
            
            nearest_district = None
            min_distance = float('inf')
            
            # 각 상권과의 거리 계산
            for i, district in enumerate(district_clusters):
                try:
                    distance = DistrictService.calculate_distance(
                        store_y, store_x,  # 매장 좌표
                        float(district.y), float(district.x)  # 상권 좌표
                    )
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_district = district
                        
                    if i < 3:  # 처음 3개만 로그 출력
                        print(f"  District {district.district_code}: distance={distance:.2f}m")
                        
                except Exception as e:
                    print(f"❌ Error calculating distance for {district.district_code}: {e}")
                    continue
            
            if nearest_district:
                result = {
                    "district_code": nearest_district.district_code,
                    "district_name": nearest_district.district_name,
                    "district_cluster_label": nearest_district.cluster_label,
                    "district_cluster_type": nearest_district.cluster_type,
                    "distance_meters": round(min_distance, 2)
                }
                print(f"✅ Found nearest district: {result}")
                return result
            else:
                print("⚠️  No nearest district found")
                return None
                
        except Exception as e:
            print(f"❌ Error in find_nearest_district_cluster: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def get_district_info(db: Session, district_code: str) -> Optional[Dict]:
        """
        상권 코드로 상권 정보 조회
        
        Returns:
            Dict with district info or None
        """
        try:
            print(f"🔍 Looking up district info for: '{district_code}'")
            
            district_cluster = (
                db.query(DistrictCluster)
                .filter(DistrictCluster.district_code == district_code)
                .first()
            )
            
            if not district_cluster:
                print(f"⚠️  District '{district_code}' not found in district_clusters table")
                return None
            
            result = {
                "district_code": district_cluster.district_code,
                "district_name": district_cluster.district_name,
                "cluster_label": district_cluster.cluster_label,
                "cluster_type": district_cluster.cluster_type,
                "total_revenue": int(district_cluster.total_revenue),
                "avg_age": float(district_cluster.avg_age),
                "efficiency": float(district_cluster.efficiency),
                "business_count": district_cluster.business_count,
                "coordinates": {
                    "latitude": float(district_cluster.y) if district_cluster.y else None,
                    "longitude": float(district_cluster.x) if district_cluster.x else None
                }
            }
            
            print(f"✅ District info found: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error in get_district_info: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def get_industry_cluster_info(db: Session, industry_name: str) -> Optional[Dict]:
        """
        업종명으로 업종 클러스터 정보 조회
        
        Returns:
            Dict with industry cluster info or None
        """
        try:
            print(f"🔍 Looking up industry cluster for: '{industry_name}'")
            
            industry_cluster = (
                db.query(IndustryCluster)
                .filter(IndustryCluster.industry_name == industry_name)
                .first()
            )
            
            if not industry_cluster:
                print(f"⚠️  Industry '{industry_name}' not found in industry_clusters table")
                
                # 유사한 업종명 찾기 (디버깅용)
                similar_industries = (
                    db.query(IndustryCluster.industry_name)
                    .filter(IndustryCluster.industry_name.like(f"%{industry_name}%"))
                    .limit(5)
                    .all()
                )
                
                if similar_industries:
                    similar_names = [row[0] for row in similar_industries]
                    print(f"💡 Similar industries found: {similar_names}")
                else:
                    # 전체 업종 목록 확인 (처음 5개)
                    all_industries = (
                        db.query(IndustryCluster.industry_name)
                        .limit(5)
                        .all()
                    )
                    if all_industries:
                        all_names = [row[0] for row in all_industries]
                        print(f"📋 Available industries (first 5): {all_names}")
                    
                return None
            
            result = {
                "industry_cluster_label": industry_cluster.cluster_label,
                "industry_cluster_type": industry_cluster.industry_type_code,
            }
            
            print(f"✅ Industry cluster found: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error in get_industry_cluster_info: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None
