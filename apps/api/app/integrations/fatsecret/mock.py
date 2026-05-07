from __future__ import annotations

from app.integrations.fatsecret import FoodItem

# 30 deterministic food items (hash-stable IDs)
_ITEMS: list[FoodItem] = [
    # 사람 음식 (12)
    FoodItem(
        food_id="mock-f001",
        name="닭가슴살",
        brand=None,
        kcal_per_100g=165.0,
        protein_g=31.0,
        carbs_g=0.0,
        fat_g=3.6,
    ),
    FoodItem(
        food_id="mock-f002",
        name="사과",
        brand=None,
        kcal_per_100g=52.0,
        protein_g=0.3,
        carbs_g=14.0,
        fat_g=0.2,
    ),
    FoodItem(
        food_id="mock-f003",
        name="사과주스",
        brand=None,
        kcal_per_100g=46.0,
        protein_g=0.1,
        carbs_g=11.4,
        fat_g=0.1,
    ),
    FoodItem(
        food_id="mock-f004",
        name="김밥",
        brand=None,
        kcal_per_100g=162.0,  # 추정
        protein_g=5.5,
        carbs_g=28.0,
        fat_g=3.5,
    ),
    FoodItem(
        food_id="mock-f005",
        name="비빔밥",
        brand=None,
        kcal_per_100g=130.0,  # 추정
        protein_g=5.0,
        carbs_g=22.0,
        fat_g=2.5,
    ),
    FoodItem(
        food_id="mock-f006",
        name="스테이크",
        brand=None,
        kcal_per_100g=271.0,
        protein_g=26.0,
        carbs_g=0.0,
        fat_g=18.0,
    ),
    FoodItem(
        food_id="mock-f007",
        name="토마토",
        brand=None,
        kcal_per_100g=18.0,
        protein_g=0.9,
        carbs_g=3.9,
        fat_g=0.2,
    ),
    FoodItem(
        food_id="mock-f008",
        name="바나나",
        brand=None,
        kcal_per_100g=89.0,
        protein_g=1.1,
        carbs_g=23.0,
        fat_g=0.3,
    ),
    FoodItem(
        food_id="mock-f009",
        name="우유",
        brand=None,
        kcal_per_100g=61.0,
        protein_g=3.2,
        carbs_g=4.8,
        fat_g=3.3,
    ),
    FoodItem(
        food_id="mock-f010",
        name="식빵",
        brand=None,
        kcal_per_100g=265.0,
        protein_g=9.0,
        carbs_g=49.0,
        fat_g=3.2,
    ),
    FoodItem(
        food_id="mock-f011",
        name="계란",
        brand=None,
        kcal_per_100g=155.0,
        protein_g=13.0,
        carbs_g=1.1,
        fat_g=11.0,
    ),
    FoodItem(
        food_id="mock-f012",
        name="고구마",
        brand=None,
        kcal_per_100g=86.0,
        protein_g=1.6,
        carbs_g=20.0,
        fat_g=0.1,
    ),
    # 반려견 사료 (6)
    FoodItem(
        food_id="mock-d001",
        name="로얄캐닌 어덜트",
        brand="Royal Canin",
        kcal_per_100g=363.0,  # 추정
        protein_g=25.0,
        carbs_g=35.0,
        fat_g=14.0,
    ),
    FoodItem(
        food_id="mock-d002",
        name="로얄캐닌 미니어덜트",
        brand="Royal Canin",
        kcal_per_100g=374.0,  # 추정
        protein_g=26.0,
        carbs_g=34.0,
        fat_g=16.0,
    ),
    FoodItem(
        food_id="mock-d003",
        name="힐스 사이언스 다이어트 어덜트",
        brand="Hill's Science Diet",
        kcal_per_100g=349.0,  # 추정
        protein_g=22.0,
        carbs_g=40.0,
        fat_g=12.0,
    ),
    FoodItem(
        food_id="mock-d004",
        name="오리젠 오리지널",
        brand="Orijen",
        kcal_per_100g=392.0,  # 추정
        protein_g=38.0,
        carbs_g=20.0,
        fat_g=18.0,
    ),
    FoodItem(
        food_id="mock-d005",
        name="아카나 어덜트",
        brand="Acana",
        kcal_per_100g=378.0,  # 추정
        protein_g=31.0,
        carbs_g=26.0,
        fat_g=17.0,
    ),
    FoodItem(
        food_id="mock-d006",
        name="내추럴발란스 LID 양고기",
        brand="Natural Balance",
        kcal_per_100g=341.0,  # 추정
        protein_g=21.0,
        carbs_g=38.0,
        fat_g=11.0,
    ),
    # 반려견 간식 (3)
    FoodItem(
        food_id="mock-t001",
        name="덴타스틱 미디엄",
        brand="Pedigree",
        kcal_per_100g=330.0,  # 추정
        protein_g=8.0,
        carbs_g=60.0,
        fat_g=6.0,
    ),
    FoodItem(
        food_id="mock-t002",
        name="동결건조 닭가슴살 간식",
        brand=None,
        kcal_per_100g=420.0,  # 추정
        protein_g=70.0,
        carbs_g=2.0,
        fat_g=12.0,
    ),
    FoodItem(
        food_id="mock-t003",
        name="양고기 트릿",
        brand=None,
        kcal_per_100g=380.0,  # 추정
        protein_g=50.0,
        carbs_g=8.0,
        fat_g=18.0,
    ),
    # 처방식 (3)
    FoodItem(
        food_id="mock-p001",
        name="힐스 r/d",
        brand="Hill's",
        kcal_per_100g=264.0,  # 추정
        protein_g=19.0,
        carbs_g=38.0,
        fat_g=7.0,
    ),
    FoodItem(
        food_id="mock-p002",
        name="로얄캐닌 HP 가수분해",
        brand="Royal Canin",
        kcal_per_100g=358.0,  # 추정
        protein_g=20.0,
        carbs_g=42.0,
        fat_g=12.0,
    ),
    FoodItem(
        food_id="mock-p003",
        name="로얄캐닌 신장 처방식",
        brand="Royal Canin",
        kcal_per_100g=340.0,  # 추정
        protein_g=14.0,
        carbs_g=46.0,
        fat_g=12.0,
    ),
    # 일반식 (6)
    FoodItem(
        food_id="mock-g001",
        name="두부",
        brand=None,
        kcal_per_100g=76.0,
        protein_g=8.0,
        carbs_g=1.9,
        fat_g=4.2,
    ),
    FoodItem(
        food_id="mock-g002",
        name="브로콜리 (찐)",
        brand=None,
        kcal_per_100g=35.0,
        protein_g=2.4,
        carbs_g=7.2,
        fat_g=0.4,
    ),
    FoodItem(
        food_id="mock-g003",
        name="호박 (찐)",
        brand=None,
        kcal_per_100g=26.0,  # 추정
        protein_g=1.0,
        carbs_g=6.5,
        fat_g=0.1,
    ),
    FoodItem(
        food_id="mock-g004",
        name="당근 (찐)",
        brand=None,
        kcal_per_100g=35.0,
        protein_g=0.8,
        carbs_g=8.2,
        fat_g=0.2,
    ),
    FoodItem(
        food_id="mock-g005",
        name="닭가슴살 (찐)",
        brand=None,
        kcal_per_100g=150.0,  # 추정
        protein_g=30.0,
        carbs_g=0.0,
        fat_g=2.5,
    ),
    FoodItem(
        food_id="mock-g006",
        name="연어 (구운)",
        brand=None,
        kcal_per_100g=208.0,
        protein_g=20.0,
        carbs_g=0.0,
        fat_g=13.0,
    ),
]

_INDEX: dict[str, FoodItem] = {item.food_id: item for item in _ITEMS}


class MockFoodProvider:
    """Deterministic mock food provider with 30 preset items."""

    async def search(self, q: str, locale: str = "ko_KR") -> list[FoodItem]:
        q_lower = q.lower()
        return [
            item
            for item in _ITEMS
            if q_lower in item.name.lower() or (item.brand and q_lower in item.brand.lower())
        ]

    async def get(self, food_id: str) -> FoodItem | None:
        return _INDEX.get(food_id)
