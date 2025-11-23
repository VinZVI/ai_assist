"""
@file: handlers/subscription.py
@description: Обработчики команд подписки
@dependencies: aiogram, app.services.subscription_service, app.subscription_config.subscription_config
@created: 2025-11-22
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.services.subscription_service import SubscriptionService
from app.subscription_config import SubscriptionTier
from app.subscription_config import SubscriptionConfig
from app.models.user import User


class SubscriptionHandler:
    """Обработчик команд подписки"""

    def __init__(self, subscription_service: SubscriptionService):
        self.subscription_service = subscription_service

    async def handle_subscription_status(self, message: Message, user: User):
        """Показ статуса подписки"""
        stats = await self.subscription_service.get_usage_stats(user.telegram_id)

        status_message = self.format_subscription_status(stats)
        keyboard = self.create_subscription_keyboard(stats['tier'])

        await message.answer(
            text=status_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    def format_subscription_status(self, stats: dict) -> str:
        """Форматирование статуса подписки"""
        tier_names = {
            'free': '🆓 Без подписки',
            'standard': '⭐ Стандарт',
            'premium': '💎 Премиум',
            'deluxe': '👑 Deluxe',
            'admin': '🛡️ Админ'
        }

        tier_name = tier_names.get(stats['tier'], stats['tier'])

        message = f"""
<b>{tier_name}</b>

📨 Сообщения: {stats['messages']['used']}"""

        if stats['messages']['unlimited']:
            message += " (безлимит)"
        else:
            message += f"/{stats['messages']['limit']}"

        if stats['images']['limit'] > 0 or stats['images']['unlimited']:
            message += f"\n🖼️ Изображения: {stats['images']['used']}"
            if stats['images']['unlimited']:
                message += " (безлимит)"
            else:
                message += f"/{stats['images']['limit']}"

        if stats['expires_at']:
            message += f"\n⏰ До окончания: {stats['days_remaining']} дн."

        return message

    def create_subscription_keyboard(self, current_tier: str):
        """Создание клавиатуры для выбора подписки"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Получаем доступные уровни подписки
        available_tiers = [
            SubscriptionTier.STANDARD,
            SubscriptionTier.PREMIUM,
            SubscriptionTier.DELUXE
        ]
        
        # Создаем кнопки для каждого уровня, кроме текущего
        buttons = []
        for tier in available_tiers:
            if tier.value != current_tier:
                price = SubscriptionConfig.get_tier_price(tier)
                tier_name = {
                    'standard': '⭐ Стандарт',
                    'premium': '💎 Премиум',
                    'deluxe': '👑 Deluxe'
                }.get(tier.value, tier.value)
                
                button = InlineKeyboardButton(
                    text=f"{tier_name} ({price} ⭐)",
                    callback_data=f"upgrade:{tier.value}"
                )
                buttons.append([button])

        if buttons:
            buttons.append([
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_upgrade"
                )
            ])
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        
        return None

    async def handle_upgrade_callback(self, callback: CallbackQuery, user: User):
        """Обработка выбора уровня подписки"""
        tier_str = callback.data.split(":")[1]
        tier = SubscriptionTier(tier_str)

        # Создаем счет для оплаты
        price = SubscriptionConfig.get_tier_price(tier)

        if price > 0:
            await self.create_payment_invoice(callback, user, tier, price)
        else:
            await callback.answer("Этот уровень недоступен для покупки")

    async def create_payment_invoice(self, callback: CallbackQuery, user: User, tier: SubscriptionTier, price: int):
        """Создание счета для оплаты подписки"""
        tier_names = {
            'standard': '⭐ Стандарт',
            'premium': '💎 Премиум',
            'deluxe': '👑 Deluxe'
        }
        
        tier_name = tier_names.get(tier.value, tier.value)
        
        try:
            # Создаем счет на оплату через Telegram Stars
            prices = [{"label": f"Подписка {tier_name}", "amount": price}]
            
            invoice = await callback.bot.send_invoice(
                chat_id=user.telegram_id,
                title=f"Подписка {tier_name}",
                description=f"Подписка {tier_name} на 30 дней",
                payload=f"subscription_{tier.value}_{user.telegram_id}",
                provider_token="",  # Для Telegram Stars оставляем пустым
                currency="XTR",  # Telegram Stars
                prices=prices,
                start_parameter=f"subscription_{tier.value}",
                provider_data={}
            )
            
            await callback.answer("Счет на оплату создан!")
        except Exception as e:
            await callback.answer(f"Ошибка при создании счета: {str(e)}")

    async def handle_payment_success(self, message: Message, user: User, payload: str):
        """Обработка успешной оплаты подписки"""
        try:
            # Разбираем payload
            parts = payload.split("_")
            if len(parts) >= 3 and parts[0] == "subscription":
                tier_str = parts[1]
                tier = SubscriptionTier(tier_str)
                
                # Обновляем подписку пользователя
                payment_data = {
                    "provider": "telegram_stars",
                    "external_id": message.successful_payment.telegram_payment_charge_id
                }
                
                subscription = await self.subscription_service.upgrade_subscription(
                    user.telegram_id,
                    tier,
                    payment_data
                )
                
                tier_names = {
                    'standard': '⭐ Стандарт',
                    'premium': '💎 Премиум',
                    'deluxe': '👑 Deluxe'
                }
                
                tier_name = tier_names.get(tier.value, tier.value)
                
                success_message = f"""
🎉 Поздравляем! 

Вы успешно приобрели подписку {tier_name}!
                
Ваши преимущества теперь активны:
• Увеличенный лимит сообщений
• Приоритет в обработке запросов
• Без рекламы
• Расширенные возможности

Спасибо за ваш выбор! 🙏
                """
                
                await message.answer(success_message)
            else:
                await message.answer("Ошибка обработки платежа. Пожалуйста, свяжитесь с поддержкой.")
        except Exception as e:
            await message.answer(f"Ошибка при обработке платежа: {str(e)}")

    async def handle_cancel_upgrade(self, callback: CallbackQuery):
        """Обработка отмены апгрейда"""
        await callback.message.delete()
        await callback.answer("Апгрейд отменен")


def register_subscription_handlers(router: Router, subscription_service: SubscriptionService):
    """Регистрация обработчиков подписки"""
    handler = SubscriptionHandler(subscription_service)
    
    router.message.register(handler.handle_subscription_status, Command("subscription"))
    router.callback_query.register(handler.handle_upgrade_callback, F.data.startswith("upgrade:"))
    router.callback_query.register(handler.handle_cancel_upgrade, F.data == "cancel_upgrade")
    
    return handler


# Экспорт для удобного использования
__all__ = ["SubscriptionHandler", "register_subscription_handlers"]