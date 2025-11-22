"""
@file: services/chat_service.py
@description: Сервис управления чатами
@dependencies: sqlalchemy, app.models.chat, app.models.chat_message
@created: 2025-11-22
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Chat
from app.models.chat_message import ChatMessage
from app.models.character import Character
from app.models.scenario import Scenario


class ChatService:
    """Сервис управления чатами"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_chat(
        self,
        user_id: int,
        character_id: int,
        scenario_id: Optional[int] = None,
        retention_days: Optional[int] = None
    ) -> Optional[Chat]:
        """Создание нового чата"""
        # Проверяем существование персонажа
        character = await self.db.get(Character, character_id)
        if not character or not character.is_active:
            return None
        
        # Проверяем существование сценария (если указан)
        scenario = None
        if scenario_id:
            scenario = await self.db.get(Scenario, scenario_id)
            if not scenario or not scenario.is_active:
                return None
        
        # Создаем новый чат
        chat = Chat(
            user_id=user_id,
            character_id=character_id,
            scenario_id=scenario_id,
            memory_retention_days=retention_days,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)
        
        # Обновляем статистику персонажа
        character.total_chats += 1
        await self.db.commit()
        await self.db.refresh(character)
        
        # Обновляем статистику сценария (если указан)
        if scenario:
            scenario.total_chats += 1
            await self.db.commit()
            await self.db.refresh(scenario)
        
        return chat

    async def get_user_chats(
        self,
        user_id: int,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chat]:
        """Получение чатов пользователя"""
        stmt = select(Chat).where(Chat.user_id == user_id)
        
        if active_only:
            stmt = stmt.where(Chat.is_active == True)
        
        stmt = stmt.order_by(desc(Chat.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_chat_with_details(self, chat_id: int, user_id: int) -> Optional[Chat]:
        """Получение чата с деталями (персонаж, сценарий)"""
        stmt = (
            select(Chat)
            .where(Chat.id == chat_id, Chat.user_id == user_id)
            .options(
                selectinload(Chat.character),
                selectinload(Chat.scenario),
                selectinload(Chat.messages)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chat_messages(
        self,
        chat_id: int,
        limit: int = 50,
        offset: int = 0,
        exclude_deleted: bool = True
    ) -> List[ChatMessage]:
        """Получение сообщений чата"""
        stmt = select(ChatMessage).where(ChatMessage.chat_id == chat_id)
        
        if exclude_deleted:
            stmt = stmt.where(ChatMessage.is_deleted == False)
        
        stmt = (
            stmt
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self,
        chat_id: int,
        message_type: str,
        content: str,
        extra_data: Optional[dict] = None,
        ai_model: Optional[str] = None,
        generation_time_ms: Optional[int] = None,
        token_count: Optional[int] = None
    ) -> Optional[ChatMessage]:
        """Добавление сообщения в чат"""
        # Проверяем существование чата
        chat = await self.db.get(Chat, chat_id)
        if not chat or not chat.is_active:
            return None
        
        # Создаем новое сообщение
        message = ChatMessage(
            chat_id=chat_id,
            message_type=message_type,
            content=content,
            extra_data=extra_data,
            ai_model=ai_model,
            generation_time_ms=generation_time_ms,
            token_count=token_count,
            created_at=datetime.utcnow(),
            is_deleted=False
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        # Обновляем статистику чата
        chat.total_messages += 1
        if message_type == "user":
            chat.user_messages_count += 1
        elif message_type == "ai":
            chat.ai_messages_count += 1
        chat.last_message_at = datetime.utcnow()
        chat.updated_at = datetime.utcnow()
        
        # Обновляем статистику персонажа
        character = await self.db.get(Character, chat.character_id)
        if character:
            character.total_messages += 1
            await self.db.commit()
            await self.db.refresh(character)
        
        # Обновляем статистику сценария (если есть)
        if chat.scenario_id:
            scenario = await self.db.get(Scenario, chat.scenario_id)
            if scenario:
                scenario.total_messages += 1
                await self.db.commit()
                await self.db.refresh(scenario)
        
        await self.db.commit()
        await self.db.refresh(chat)
        
        return message

    async def delete_message(self, message_id: int, user_id: int) -> bool:
        """Пометка сообщения как удаленного"""
        stmt = select(ChatMessage).join(Chat).where(
            ChatMessage.id == message_id,
            Chat.user_id == user_id
        )
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if message:
            message.is_deleted = True
            await self.db.commit()
            return True
        
        return False

    async def cleanup_expired_chats(self) -> int:
        """Очистка просроченных чатов"""
        # Получаем все активные чаты с установленным сроком хранения
        stmt = select(Chat).where(
            and_(
                Chat.is_active == True,
                Chat.memory_retention_days.isnot(None),
                Chat.last_message_at.isnot(None)
            )
        )
        result = await self.db.execute(stmt)
        chats = result.scalars().all()
        
        deleted_count = 0
        for chat in chats:
            if chat.should_expire:
                chat.is_active = False
                deleted_count += 1
        
        if deleted_count > 0:
            await self.db.commit()
        
        return deleted_count

    async def get_active_chat_count(self, user_id: int) -> int:
        """Получение количества активных чатов пользователя"""
        stmt = select(Chat).where(
            and_(
                Chat.user_id == user_id,
                Chat.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def update_chat_title(self, chat_id: int, user_id: int, title: str) -> bool:
        """Обновление заголовка чата"""
        stmt = select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == user_id
        )
        result = await self.db.execute(stmt)
        chat = result.scalar_one_or_none()
        
        if chat:
            chat.title = title
            chat.updated_at = datetime.utcnow()
            await self.db.commit()
            return True
        
        return False


# Экспорт для удобного использования
__all__ = ["ChatService"]