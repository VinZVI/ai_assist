"""
@file: services/character_service.py
@description: Сервис управления персонажами
@dependencies: sqlalchemy, app.models.character, app.models.character_tag, app.models.character_rating
@created: 2025-11-22
"""

from datetime import UTC, datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.character import Character
from app.models.character_rating import CharacterRating
from app.models.character_tag import CharacterTag


class CharacterService:
    """Сервис управления персонажами"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_popular_characters(self, limit: int = 10) -> list[Character]:
        """Получение популярных персонажей"""
        stmt = (
            select(Character)
            .where(Character.is_active == True)
            .order_by(desc(Character.popularity_score))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_characters(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        gender: str | None = None,
        age_range: tuple[int, int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Character]:
        """Поиск персонажей с фильтрами"""
        stmt = select(Character).where(Character.is_active == True)

        # Поиск по имени
        if query:
            stmt = stmt.where(Character.name.ilike(f"%{query}%"))

        # Фильтр по полу
        if gender:
            stmt = stmt.where(Character.gender == gender)

        # Фильтр по возрасту
        if age_range:
            min_age, max_age = age_range
            stmt = stmt.where(Character.age >= min_age, Character.age <= max_age)

        # Фильтр по тегам
        if tags:
            stmt = stmt.join(CharacterTag).where(CharacterTag.tag_name.in_(tags))

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_character_with_stats(self, character_id: int) -> Character | None:
        """Получение персонажа со статистикой"""
        stmt = (
            select(Character)
            .where(Character.id == character_id, Character.is_active == True)
            .options(selectinload(Character.tags), selectinload(Character.ratings))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def rate_character(
        self, character_id: int, user_id: int, rating: int
    ) -> bool:
        """Оценка персонажа пользователем"""
        # Проверяем, что рейтинг в допустимом диапазоне
        if rating < 1 or rating > 5:
            return False

        # Проверяем существование персонажа
        character = await self.db.get(Character, character_id)
        if not character:
            return False

        # Проверяем существование оценки от этого пользователя
        stmt = select(CharacterRating).where(
            CharacterRating.character_id == character_id,
            CharacterRating.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        existing_rating = result.scalar_one_or_none()

        if existing_rating:
            # Обновляем существующую оценку
            old_rating = existing_rating.rating
            existing_rating.rating = rating
            existing_rating.created_at = datetime.now(UTC)

            # Обновляем статистику персонажа
            character.rating_sum = character.rating_sum - old_rating + rating
        else:
            # Создаем новую оценку
            new_rating = CharacterRating(
                character_id=character_id, user_id=user_id, rating=rating
            )
            self.db.add(new_rating)

            # Обновляем статистику персонажа
            character.rating_sum += rating
            character.rating_count += 1

        await self.db.commit()
        await self.db.refresh(character)
        return True

    async def get_character_tags(self, character_id: int) -> list[str]:
        """Получение тегов персонажа"""
        stmt = select(CharacterTag.tag_name).where(
            CharacterTag.character_id == character_id
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def add_character_tag(self, character_id: int, tag_name: str) -> bool:
        """Добавление тега к персонажу"""
        # Проверяем существование персонажа
        character = await self.db.get(Character, character_id)
        if not character:
            return False

        # Проверяем, существует ли уже такой тег
        stmt = select(CharacterTag).where(
            CharacterTag.character_id == character_id, CharacterTag.tag_name == tag_name
        )
        result = await self.db.execute(stmt)
        existing_tag = result.scalar_one_or_none()

        if not existing_tag:
            tag = CharacterTag(character_id=character_id, tag_name=tag_name)
            self.db.add(tag)
            await self.db.commit()
            return True

        return False

    async def remove_character_tag(self, character_id: int, tag_name: str) -> bool:
        """Удаление тега у персонажа"""
        stmt = select(CharacterTag).where(
            CharacterTag.character_id == character_id, CharacterTag.tag_name == tag_name
        )
        result = await self.db.execute(stmt)
        tag = result.scalar_one_or_none()

        if tag:
            await self.db.delete(tag)
            await self.db.commit()
            return True

        return False


# Экспорт для удобного использования
__all__ = ["CharacterService"]
