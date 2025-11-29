# Карта навигации и требуемая бизнес-логика

## 📱 Карта навигации пользователей

### Главное меню (`main_menu`)
**Реализовано:** ✅ Полностью
- **💬 Начать диалог** (`start_chat`) → Приветственное сообщение для начала AI диалога
- **👤 Мой профиль** (`my_stats`) → Переход в статистику пользователя  
- **⭐ Премиум** (`premium_info`) → Информация о премиум доступе
- **❓ Помощь** (`help`) → Справочная система
- **📊 Лимиты** (`settings`) → Системные настройки

### Профиль пользователя (`my_stats`)
**Реализовано:** ⚠️ Частично (1 из 3)
- **📈 Детальная статистика** (`detailed_stats`) → ❌ Заглушка
- **🏆 Мои достижения** (`achievements`) → ❌ Заглушка  
- **🏠 Главное меню** (`main_menu`) → ✅ Возврат в главное меню

### Премиум доступ (`premium_info`)
**Реализовано:** ⚠️ Частично (1 из 4)
- **💳 Купить премиум** (`buy_premium:{price}`) → ❌ Заглушка
- **📜 Что даёт премиум?** (`premium_features`) → ❌ Заглушка
- **❓ FAQ** (`premium_faq`) → ❌ Заглушка
- **🔙 Назад в меню** (`main_menu`) → ✅ Возврат в главное меню

### Справка (`help`)
**Реализовано:** ⚠️ Частично (1 из 5)
- **📚 Руководство** (`help_guide`) → ❌ Заглушка
- **❓ FAQ** (`help_faq`) → ❌ Заглушка
- **📞 Поддержка** (`help_support`) → ❌ Заглушка
- **🐛 Сообщить об ошибке** (`help_bug_report`) → ❌ Заглушка
- **🏠 Главное меню** (`main_menu`) → ✅ Возврат в главное меню

### Настройки (`settings`)
**Реализовано:** ⚠️ Частично (2 из 4)
- **🌍 Язык** (`settings_language`) → ✅ Выбор языка RU/EN
- **🔔 Уведомления** (`settings_notifications`) → ❌ Заглушка
- **🗑️ Удалить данные** (`settings_delete_data`) → ❌ Заглушка
- **🏠 Главное меню** (`main_menu`) → ✅ Возврат в главное меню

#### Выбор языка (`settings_language`)
**Реализовано:** ✅ Полностью
- **🇷🇺 Русский** (`select_language:ru`) → ✅ Смена на русский
- **🇺🇸 English** (`select_language:en`) → ✅ Смена на английский  
- **🔙 Назад** (`settings`) → ✅ Возврат в настройки

---

## 🔧 Требуемая бизнес-логика для реализации

### 1. Детальная статистика (`detailed_stats`)

**Файл:** `app/handlers/stats.py`
```python
@callback_router.callback_query(F.data == "detailed_stats")
async def show_detailed_stats(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    # Статистика сообщений
    daily_stats = await get_daily_message_stats(user.id, days=7)
    monthly_stats = await get_monthly_message_stats(user.id, months=3)
    
    # AI статистика
    ai_stats = await get_ai_usage_stats(user.id)
    
    # Время активности
    activity_pattern = await get_user_activity_pattern(user.id)
    
    stats_text = format_detailed_stats(daily_stats, monthly_stats, ai_stats, activity_pattern)
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=create_detailed_stats_keyboard(user.language_code)
    )
```

**Требуемые функции БД:**
```python
# app/services/stats_service.py
async def get_daily_message_stats(user_id: int, days: int = 7):
    """Статистика сообщений по дням"""
    async with get_session() as session:
        stmt = select(
            func.date(Conversation.created_at).label('date'),
            func.count().label('messages'),
            func.sum(Conversation.tokens_used).label('tokens')
        ).where(
            Conversation.user_id == user_id,
            Conversation.created_at >= datetime.now() - timedelta(days=days)
        ).group_by(func.date(Conversation.created_at))
        
        return await session.execute(stmt)

async def get_ai_usage_stats(user_id: int):
    """Статистика использования AI"""
    async with get_session() as session:
        stmt = select(
            Conversation.ai_model,
            func.count().label('usage_count'),
            func.sum(Conversation.tokens_used).label('total_tokens'),
            func.avg(Conversation.response_time).label('avg_response_time')
        ).where(
            Conversation.user_id == user_id
        ).group_by(Conversation.ai_model)
        
        return await session.execute(stmt)
```

### 2. Система достижений (`achievements`)

**Файл:** `app/models/achievement.py`
```python
class Achievement(Base):
    __tablename__ = "achievements"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(50))  # emoji
    condition_type: Mapped[str] = mapped_column(String(50))  # "message_count", "daily_streak"
    condition_value: Mapped[int] = mapped_column()
    reward_type: Mapped[str] = mapped_column(String(50), nullable=True)  # "premium_days"
    reward_value: Mapped[int] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    earned_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped[Achievement] = relationship()
```

**Сервис достижений:**
```python
# app/services/achievement_service.py
class AchievementService:
    async def check_user_achievements(self, user_id: int):
        """Проверка новых достижений пользователя"""
        user_stats = await self.get_user_stats(user_id)
        available_achievements = await self.get_available_achievements(user_id)
        
        new_achievements = []
        for achievement in available_achievements:
            if await self.check_achievement_condition(user_stats, achievement):
                await self.award_achievement(user_id, achievement.id)
                new_achievements.append(achievement)
        
        return new_achievements
    
    async def check_achievement_condition(self, user_stats: dict, achievement: Achievement):
        """Проверка условия достижения"""
        if achievement.condition_type == "message_count":
            return user_stats['total_messages'] >= achievement.condition_value
        elif achievement.condition_type == "daily_streak":
            return user_stats['daily_streak'] >= achievement.condition_value
        elif achievement.condition_type == "premium_purchase":
            return user_stats['has_premium'] == True
        return False

# Примеры достижений
ACHIEVEMENTS = [
    {"name": "Первый шаг", "description": "Отправил первое сообщение", "icon": "👋", "condition_type": "message_count", "condition_value": 1},
    {"name": "Болтун", "description": "Отправил 100 сообщений", "icon": "💬", "condition_type": "message_count", "condition_value": 100},
    {"name": "Преданный", "description": "7 дней подряд активности", "icon": "🔥", "condition_type": "daily_streak", "condition_value": 7},
    {"name": "VIP", "description": "Купил премиум доступ", "icon": "⭐", "condition_type": "premium_purchase", "condition_value": 1}
]
```

### 3. Платежная система (`buy_premium`)

**Файл:** `app/services/payment_service.py`
```python
from aiogram.types import LabeledPrice, SuccessfulPayment

class PaymentService:
    async def create_telegram_stars_invoice(self, user_id: int, amount: int, duration_days: int):
        """Создание инвойса для Telegram Stars"""
        invoice = await bot.send_invoice(
            chat_id=user_id,
            title="AI-Компаньон Премиум",
            description=f"Премиум доступ на {duration_days} дней",
            payload=f"premium_{user_id}_{duration_days}",
            provider_token="",  # Пустой для Telegram Stars
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label="Премиум", amount=amount)],
            start_parameter="premium_purchase"
        )
        return invoice
    
    async def handle_successful_payment(self, payment: SuccessfulPayment, user_id: int):
        """Обработка успешного платежа"""
        # Парсим payload
        _, user_id_str, duration_str = payment.invoice_payload.split("_")
        duration_days = int(duration_str)
        
        # Активируем премиум
        await self.activate_premium(int(user_id_str), duration_days)
        
        # Логируем платеж
        await self.log_payment(user_id, payment.total_amount, payment.telegram_payment_charge_id)
    
    async def activate_premium(self, user_id: int, duration_days: int):
        """Активация премиум доступа"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            
            # Если уже есть премиум - продлеваем
            if user.premium_until and user.premium_until > datetime.utcnow():
                new_premium_until = user.premium_until + timedelta(days=duration_days)
            else:
                new_premium_until = datetime.utcnow() + timedelta(days=duration_days)
            
            user.premium_until = new_premium_until
            user.is_premium = True
            
            await session.commit()
```

### 4. Настройки уведомлений (`settings_notifications`)

**Добавление в модель User:**
```python
# app/models/user.py
class User(Base):
    # ... существующие поля ...
    
    # Настройки уведомлений
    notifications_enabled: Mapped[bool] = mapped_column(default=True)
    marketing_notifications: Mapped[bool] = mapped_column(default=True) 
    reminder_notifications: Mapped[bool] = mapped_column(default=True)
    achievement_notifications: Mapped[bool] = mapped_column(default=True)
```

**Обработчик настроек:**
```python
@callback_router.callback_query(F.data == "settings_notifications")
async def show_notification_settings(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    settings_text = format_notification_settings(user)
    keyboard = create_notification_settings_keyboard(user)
    
    await callback.message.edit_text(settings_text, reply_markup=keyboard)

def create_notification_settings_keyboard(user: User):
    builder = InlineKeyboardBuilder()
    
    # Переключатели для каждого типа уведомлений
    builder.row(
        InlineKeyboardButton(
            text=f"🔔 Все уведомления: {'✅' if user.notifications_enabled else '❌'}",
            callback_data="toggle_notifications_all"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📢 Маркетинговые: {'✅' if user.marketing_notifications else '❌'}",
            callback_data="toggle_notifications_marketing"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"⏰ Напоминания: {'✅' if user.reminder_notifications else '❌'}",
            callback_data="toggle_notifications_reminder"
        )
    )
    
    return builder.as_markup()
```

### 5. Удаление данных (`settings_delete_data`)

**GDPR совместимое удаление:**
```python
@callback_router.callback_query(F.data == "settings_delete_data")
async def confirm_data_deletion(callback: CallbackQuery):
    """Первое подтверждение удаления"""
    warning_text = get_text("settings.delete_warning", callback.from_user.language_code)
    keyboard = create_delete_confirmation_keyboard(callback.from_user.language_code)
    
    await callback.message.edit_text(warning_text, reply_markup=keyboard)

@callback_router.callback_query(F.data == "confirm_delete_data")
async def final_delete_confirmation(callback: CallbackQuery):
    """Финальное подтверждение"""
    final_warning = get_text("settings.delete_final_warning", callback.from_user.language_code)
    keyboard = create_final_delete_keyboard(callback.from_user.language_code)
    
    await callback.message.edit_text(final_warning, reply_markup=keyboard)

@callback_router.callback_query(F.data == "execute_delete_data") 
async def execute_data_deletion(callback: CallbackQuery):
    """Выполнение удаления данных"""
    user_id = callback.from_user.id
    
    try:
        # Удаляем все данные пользователя
        await delete_all_user_data(user_id)
        
        # Отправляем подтверждение
        goodbye_text = get_text("settings.data_deleted", "ru")
        await callback.message.edit_text(goodbye_text)
        
        # Логируем операцию
        logger.info(f"User data deleted for user_id: {user_id}")
        
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        await callback.answer("Ошибка при удалении данных")

async def delete_all_user_data(telegram_id: int):
    """Полное удаление данных пользователя"""
    async with get_session() as session:
        # Получаем ID пользователя
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            return
        
        # Удаляем в правильном порядке (из-за foreign keys)
        await session.execute(
            delete(UserAchievement).where(UserAchievement.user_id == user.id)
        )
        await session.execute(
            delete(Conversation).where(Conversation.user_id == user.id)
        )
        await session.execute(
            delete(User).where(User.id == user.id)
        )
        
        await session.commit()
```

---

## 🔧 Административная панель

### Главное админ меню
**Доступ:** Только для админов (проверка `user.telegram_id` в `ADMIN_USER_IDS`)

**Меню управления:**
- **👥 Пользователи** → Поиск, блокировка, статистика пользователей
- **📊 Статистика** → Метрики системы, аналитика
- **💰 Платежи** → Управление подписками и платежами  
- **🔧 Система** → Мониторинг, перезапуск, конфигурация
- **📢 Рассылка** → Массовые уведомления
- **🚨 Логи** → Просмотр системных логов

### Управление пользователями (`admin_users`)

**Функции поиска и управления:**
```python
# app/handlers/admin/users.py
@admin_required
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    """Поиск пользователя по ID или username"""
    await callback.message.answer("Введите Telegram ID или @username пользователя:")
    await state.set_state(AdminStates.waiting_user_search)

@admin_required  
async def show_user_profile(callback: CallbackQuery):
    """Показ профиля пользователя с админскими действиями"""
    user_id = int(callback.data.split(":")[1])
    user = await get_user_by_id(user_id)
    
    profile_text = format_admin_user_profile(user)
    keyboard = create_admin_user_actions_keyboard(user)
    
    await callback.message.edit_text(profile_text, reply_markup=keyboard)

def create_admin_user_actions_keyboard(user: User):
    builder = InlineKeyboardBuilder()
    
    # Управление премиумом
    if user.is_premium:
        builder.row(InlineKeyboardButton(text="❌ Отключить премиум", callback_data=f"admin_remove_premium:{user.id}"))
    else:
        builder.row(InlineKeyboardButton(text="⭐ Выдать премиум", callback_data=f"admin_give_premium:{user.id}"))
    
    # Блокировка
    if user.is_blocked:
        builder.row(InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_unblock:{user.id}"))
    else:
        builder.row(InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_block:{user.id}"))
    
    # Статистика и логи
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_user_stats:{user.id}"))
    builder.row(InlineKeyboardButton(text="📄 История сообщений", callback_data=f"admin_user_messages:{user.id}"))
    
    return builder.as_markup()
```

### Системная статистика (`admin_stats`)

**Метрики для отслеживания:**
```python
# app/services/admin_stats_service.py
class AdminStatsService:
    async def get_general_stats(self):
        """Общая статистика системы"""
        async with get_session() as session:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            stats = {
                'total_users': await self._count_total_users(session),
                'active_today': await self._count_active_users(session, today),
                'active_week': await self._count_active_users(session, week_ago),
                'premium_users': await self._count_premium_users(session),
                'total_conversations': await self._count_conversations(session),
                'conversations_today': await self._count_conversations_today(session, today),
                'revenue_month': await self._calculate_monthly_revenue(session),
                'ai_requests_today': await self._count_ai_requests_today(session, today)
            }
            
            return stats
    
    async def get_growth_metrics(self, days: int = 30):
        """Метрики роста"""
        async with get_session() as session:
            # Регистрации по дням
            registrations = await session.execute(
                select(
                    func.date(User.created_at).label('date'),
                    func.count().label('registrations')
                ).where(
                    User.created_at >= datetime.now() - timedelta(days=days)
                ).group_by(func.date(User.created_at))
            )
            
            # Конверсия в премиум
            conversion_rate = await self._calculate_premium_conversion(session)
            
            return {
                'daily_registrations': registrations.all(),
                'premium_conversion_rate': conversion_rate
            }
```

### Система рассылок (`admin_broadcast`)

**Массовые уведомления:**
```python
# app/services/broadcast_service.py
class BroadcastService:
    async def create_broadcast(self, admin_id: int, message_text: str, target_audience: str):
        """Создание рассылки"""
        broadcast = Broadcast(
            admin_id=admin_id,
            message_text=message_text,
            target_audience=target_audience,  # "all", "premium", "free", "active"
            status="pending",
            created_at=datetime.utcnow()
        )
        
        async with get_session() as session:
            session.add(broadcast)
            await session.commit()
            
        # Запускаем рассылку в фоне
        asyncio.create_task(self.execute_broadcast(broadcast.id))
        
        return broadcast
    
    async def execute_broadcast(self, broadcast_id: int):
        """Выполнение рассылки"""
        async with get_session() as session:
            broadcast = await session.get(Broadcast, broadcast_id)
            users = await self.get_target_users(session, broadcast.target_audience)
            
            broadcast.status = "sending"
            broadcast.total_users = len(users)
            await session.commit()
            
            # Отправляем сообщения пакетами
            sent_count = 0
            failed_count = 0
            
            for user_batch in self.chunk_users(users, batch_size=50):
                for user in user_batch:
                    try:
                        await bot.send_message(user.telegram_id, broadcast.message_text)
                        sent_count += 1
                        await asyncio.sleep(0.1)  # Rate limiting
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Broadcast failed for user {user.id}: {e}")
                
                # Обновляем прогресс каждые 50 пользователей  
                broadcast.sent_count = sent_count
                broadcast.failed_count = failed_count
                await session.commit()
                
                await asyncio.sleep(1)  # Пауза между batch'ами
            
            broadcast.status = "completed"
            broadcast.completed_at = datetime.utcnow()
            await session.commit()
```

### Мониторинг системы (`admin_system`)

**Health checks и мониторинг:**
```python
# app/services/system_monitor.py
class SystemMonitor:
    async def get_system_health(self):
        """Комплексная проверка здоровья системы"""
        health_status = {
            'database': await self.check_database(),
            'ai_providers': await self.check_ai_providers(),
            'redis_cache': await self.check_redis(),
            'disk_space': await self.check_disk_space(),
            'memory_usage': await self.check_memory_usage(),
            'active_connections': await self.get_active_connections(),
            'response_times': await self.get_avg_response_times()
        }
        
        return health_status
    
    async def check_database(self):
        """Проверка БД"""
        try:
            async with get_session() as session:
                await session.execute(text("SELECT 1"))
                
            return {
                'status': 'healthy',
                'response_time': await self.measure_db_response_time()
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def check_ai_providers(self):
        """Проверка AI провайдеров"""
        ai_manager = get_ai_manager()
        provider_status = {}
        
        for provider_name in ai_manager.providers:
            try:
                # Тестовый запрос к провайдеру
                test_response = await ai_manager.test_provider(provider_name)
                provider_status[provider_name] = {
                    'status': 'healthy',
                    'response_time': test_response.response_time
                }
            except Exception as e:
                provider_status[provider_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return provider_status
```

Эта структура обеспечит полноценную административную панель для управления ботом и мониторинга его работы.