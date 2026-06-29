from sqlalchemy.orm import Session

from app.models.clothing_item import ClothingItem


class ShopService:
    REQUIRED_CORE_CATEGORIES = {"top", "bottom", "shoes"}

    @staticmethod
    def get_recommendations(db: Session, user_id: int):
        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        user_categories = {item.category.lower() for item in items}
        missing = ShopService.REQUIRED_CORE_CATEGORIES - user_categories
        recommendations = [
            {
                "category": category,
                "reason": "You need this to complete daily outfits",
                "priority": "high",
            }
            for category in sorted(missing)
        ]
        if not recommendations:
            recommendations.append(
                {
                    "category": "accessory",
                    "reason": "You already have the essentials. Add variety.",
                    "priority": "medium",
                }
            )
        return {"recommendations": recommendations}

