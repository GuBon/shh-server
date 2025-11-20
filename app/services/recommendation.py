from sqlalchemy.orm import Session

from app.models.user import IndustryCluster
from app.schemas.recommendation import (
    IndustryRecommendationResponse,
    IndustryRecommendationItem,
)

# 클러스터 이름 (네가 쓰던 그대로)
cluster_names = {
    0: "☕️ 2030 여성 타겟 (카페/뷰티형)",
    1: "🍺 4050 남성 타겟 (회식/식사형)",
    2: "🛍️ 4050 여성 타겟 (쇼핑/생활형)",
    3: "🎮 2030 남성 타겟 (엔터/오락형)",
}


def recommend_for_industry_db(
        db: Session,
        target_industry_name: str,
        top_n: int = 3,
) -> IndustryRecommendationResponse:
    # Lazy import to reduce startup time
    import numpy as np
    
    rows = db.query(IndustryCluster).all()
    if not rows:
        raise ValueError("industry_clusters 테이블에 데이터가 없습니다.")

    names = [r.industry_name for r in rows]
    ages = np.array([float(r.avg_age_score) for r in rows])
    female = np.array([float(r.avg_female_ratio) for r in rows])
    labels = np.array([int(r.cluster_label) for r in rows])

    if target_industry_name not in names:
        raise ValueError(f"'{target_industry_name}' 업종 데이터를 찾을 수 없습니다.")

    # 표준화
    age_mean, age_std = ages.mean(), ages.std() or 1.0
    female_mean, female_std = female.mean(), female.std() or 1.0

    scaled_age = (ages - age_mean) / age_std
    scaled_female = (female - female_mean) / female_std

    idx = names.index(target_industry_name)
    my_vec = np.array([scaled_age[idx], scaled_female[idx]])
    my_label = labels[idx]
    my_cluster_name = cluster_names.get(my_label, f"{my_label}번 그룹")

    items = []
    for i, (name, label) in enumerate(zip(names, labels)):
        if name == target_industry_name:
            continue
        if label != my_label:
            continue

        vec = np.array([scaled_age[i], scaled_female[i]])
        dist = float(np.linalg.norm(my_vec - vec))
        similarity = max(0.0, (1 - dist) * 100.0)

        comment = (
            f"{name}은(는) {cluster_names.get(label, f'{label}번 그룹')} "
            f"고객 성향과 유사하여 협업 가능성이 높습니다. "
            f"평균 연령 {ages[i]:.1f}세, 여성 비중 {female[i]:.0%}"
        )

        items.append(
            IndustryRecommendationItem(
                industryName=name,
                similarityScore=round(similarity, 1),
                avgAge=float(ages[i]),
                avgFemaleRatio=float(female[i]),
                clusterLabel=int(label),
                comment=comment,
            )
        )

    items_sorted = sorted(items, key=lambda x: -x.similarityScore)[:top_n]

    return IndustryRecommendationResponse(
        userIndustry=target_industry_name,
        clusterLabel=int(my_label),
        clusterName=my_cluster_name,
        recommendations=items_sorted,
    )

def recommend_for_industry_name(db: Session, industry_name: str, top_n: int = 3):
    # Lazy import to reduce startup time
    import numpy as np

    rows = db.query(IndustryCluster).all()
    if not rows:
        raise HTTPException(404, "industry_clusters 테이블이 비어있음")

    names = [r.industry_name for r in rows]
    ages = np.array([float(r.avg_age_score) for r in rows])
    female = np.array([float(r.avg_female_ratio) for r in rows])
    labels = np.array([int(r.cluster_label) for r in rows])

    if industry_name not in names:
        raise HTTPException(404, f"'{industry_name}' 업종을 찾을 수 없음")

    idx = names.index(industry_name)
    my_label = labels[idx]

    # 표준화
    scaled_age = (ages - ages.mean()) / (ages.std() or 1)
    scaled_female = (female - female.mean()) / (female.std() or 1)

    my_vec = np.array([scaled_age[idx], scaled_female[idx]])

    items = []
    for i, name in enumerate(names):
        if name == industry_name:
            continue
        if labels[i] != my_label:
            continue

        vec = np.array([scaled_age[i], scaled_female[i]])
        dist = float(np.linalg.norm(my_vec - vec))
        similarity = max(0, (1 - dist) * 100)

        comment = (
            f"{name}은(는) {cluster_names[labels[i]]} "
            f"고객 성향과 유사하여 협업 가능성이 높습니다. "
            f"평균 연령 {ages[i]:.1f}세, 여성 비중 {female[i]:.0%}"
        )

        items.append(
            IndustryRecommendationItem(
                industryName=name,
                similarityScore=round(similarity, 1),
                avgAge=float(ages[i]),
                avgFemaleRatio=float(female[i]),
                clusterLabel=int(labels[i]),
                comment=comment,
            )
        )

    items_sorted = sorted(items, key=lambda x: -x.similarityScore)[:top_n]

    return IndustryRecommendationResponse(
        userIndustry=industry_name,
        clusterLabel=int(my_label),
        clusterName=cluster_names.get(my_label, f"{my_label}번 그룹"),
        recommendations=items_sorted,
    )
