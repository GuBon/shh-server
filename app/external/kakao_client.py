import aiohttp
from typing import Dict, Optional, List
from app.config.settings import settings


class KakaoAPIClient:
    """카카오 Maps API 클라이언트"""

    def __init__(self):
        self.api_key = settings.KAKAO_REST_API_KEY
        self.base_url = "https://dapi.kakao.com"

    async def convert_address_to_coordinates(
        self,
        address: str
    ) -> Optional[Dict]:
        """
        주소 → 좌표 변환 (사업자 주소 검증용)

        Args:
            address: 주소

        Returns:
            좌표 정보 또는 None
        """
        url = f"{self.base_url}/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                params={"query": address}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["documents"]:
                        doc = data["documents"][0]
                        return {
                            "latitude": float(doc["y"]),
                            "longitude": float(doc["x"]),
                            "address": doc["address_name"],
                            "road_address": doc.get("road_address_name"),
                            "accuracy": "high" if doc["address_type"] == "ROAD_ADDR" else "medium"
                        }
                return None

    async def get_nearby_places(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1000,
        category: str = "FD6"
    ) -> List[Dict]:
        """
        주변 매장 정보 조회 (시장 분석용)

        Args:
            latitude: 위도
            longitude: 경도
            radius: 반경(m)
            category: 카테고리 코드

        Returns:
            매장 목록
        """
        url = f"{self.base_url}/v2/local/search/category.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}

        params = {
            "category_group_code": category,
            "x": longitude,
            "y": latitude,
            "radius": radius,
            "size": 15
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            "place_id": doc["id"],
                            "name": doc["place_name"],
                            "category": doc["category_name"],
                            "address": doc["address_name"],
                            "phone": doc.get("phone", ""),
                            "latitude": float(doc["y"]),
                            "longitude": float(doc["x"]),
                            "distance": int(doc["distance"]) if doc.get("distance") else None,
                            "place_url": doc.get("place_url", "")
                        }
                        for doc in data["documents"]
                    ]
                return []

    async def search_keyword(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[int] = None
    ) -> List[Dict]:
        """
        키워드 검색

        Args:
            query: 검색어
            latitude: 중심 위도
            longitude: 중심 경도
            radius: 반경(m)

        Returns:
            검색 결과
        """
        url = f"{self.base_url}/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}

        params = {"query": query}
        if latitude and longitude:
            params["x"] = longitude
            params["y"] = latitude
        if radius:
            params["radius"] = radius

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            "place_id": doc["id"],
                            "name": doc["place_name"],
                            "category": doc["category_name"],
                            "address": doc["address_name"],
                            "road_address": doc.get("road_address_name", ""),
                            "phone": doc.get("phone", ""),
                            "latitude": float(doc["y"]),
                            "longitude": float(doc["x"]),
                            "distance": int(doc["distance"]) if doc.get("distance") else None,
                        }
                        for doc in data["documents"]
                    ]
                return []