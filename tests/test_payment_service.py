"""
Тесты для TelegramStarsPaymentService.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import SuccessfulPayment

from app.services.payment_service import TelegramStarsPaymentService
from app.models.user import User as UserModel
from app.models.payment import Payment as PaymentModel


class TestTelegramStarsPaymentService:
    """Тесты для TelegramStarsPaymentService."""

    @pytest.fixture
    def payment_service(self) -> TelegramStarsPaymentService:
        """Фикстура для TelegramStarsPaymentService."""
        mock_bot = AsyncMock()
        return TelegramStarsPaymentService(mock_bot)

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Фикстура для мокированного пользователя."""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.telegram_id = 123456789
        user.is_premium = False
        user.premium_expires_at = None
        return user

    @pytest.fixture
    def mock_payment(self) -> MagicMock:
        """Фикстура для мокированного платежа."""
        payment = MagicMock(spec=SuccessfulPayment)
        payment.total_amount = 100
        payment.telegram_payment_charge_id = "test_payment_id"
        payment.invoice_payload = "premium_1_30"
        return payment

    @pytest.mark.asyncio
    async def test_create_invoice_success(
        self, payment_service: TelegramStarsPaymentService
    ) -> None:
        """Тест успешного создания инвойса."""
        # Arrange
        user_id = 123456789
        amount = 100
        description = "Test premium subscription"
        duration_days = 30

        # Mock the bot.send_invoice method
        payment_service.bot.send_invoice = AsyncMock(return_value=True)

        # Act
        result = await payment_service.create_invoice(
            user_id, amount, description, duration_days
        )

        # Assert
        assert result is True
        payment_service.bot.send_invoice.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_invoice_failure(
        self, payment_service: TelegramStarsPaymentService
    ) -> None:
        """Тест неудачного создания инвойса."""
        # Arrange
        user_id = 123456789
        amount = 100
        description = "Test premium subscription"
        duration_days = 30

        # Mock the bot.send_invoice method to raise an exception
        payment_service.bot.send_invoice = AsyncMock(side_effect=Exception("Test error"))

        # Act
        result = await payment_service.create_invoice(
            user_id, amount, description, duration_days
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_successful_payment_success(
        self, payment_service: TelegramStarsPaymentService, mock_payment: MagicMock
    ) -> None:
        """Тест успешной обработки платежа."""
        # Arrange
        user_telegram_id = 123456789

        # Mock the activate_premium method
        payment_service.activate_premium = AsyncMock(return_value=True)

        # Mock database session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.handle_successful_payment(
                mock_payment, user_telegram_id
            )

            # Assert
            assert result is True
            payment_service.activate_premium.assert_called_once_with(1, 30)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_successful_payment_invalid_payload(
        self, payment_service: TelegramStarsPaymentService
    ) -> None:
        """Тест обработки платежа с неверным payload."""
        # Arrange
        user_telegram_id = 123456789
        payment = MagicMock(spec=SuccessfulPayment)
        payment.total_amount = 100
        payment.telegram_payment_charge_id = "test_payment_id"
        payment.invoice_payload = "invalid_payload"

        # Act
        result = await payment_service.handle_successful_payment(
            payment, user_telegram_id
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_activate_premium_new_subscription(
        self, payment_service: TelegramStarsPaymentService, mock_user: MagicMock
    ) -> None:
        """Тест активации новой премиум подписки."""
        # Arrange
        user_id = 1
        duration_days = 30

        # Mock database session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.activate_premium(user_id, duration_days)

            # Assert
            assert result is True
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_premium_extension(
        self, payment_service: TelegramStarsPaymentService, mock_user: MagicMock
    ) -> None:
        """Тест продления существующей премиум подписки."""
        # Arrange
        user_id = 1
        duration_days = 30
        mock_user.premium_expires_at = datetime.utcnow() + timedelta(days=15)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.activate_premium(user_id, duration_days)

            # Assert
            assert result is True
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_premium_user_not_found(
        self, payment_service: TelegramStarsPaymentService
    ) -> None:
        """Тест активации премиум подписки для несуществующего пользователя."""
        # Arrange
        user_id = 999
        duration_days = 30

        # Mock database session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.activate_premium(user_id, duration_days)

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_premium_success(
        self, payment_service: TelegramStarsPaymentService
    ) -> None:
        """Тест успешной деактивации премиум подписки."""
        # Arrange
        user_id = 1

        # Mock database session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.deactivate_premium(user_id)

            # Assert
            assert result is True
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_premium_status_active(
        self, payment_service: TelegramStarsPaymentService, mock_user: MagicMock
    ) -> None:
        """Тест проверки активного премиум статуса."""
        # Arrange
        user_id = 1
        mock_user.is_premium = True
        mock_user.premium_expires_at = datetime.utcnow() + timedelta(days=30)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_user)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.check_premium_status(user_id)

            # Assert
            assert result["is_premium"] is True
            assert "expires_at" in result
            assert "remaining_days" in result

    @pytest.mark.asyncio
    async def test_check_premium_status_inactive(
        self, payment_service: TelegramStarsPaymentService, mock_user: MagicMock
    ) -> None:
        """Тест проверки неактивного премиум статуса."""
        # Arrange
        user_id = 1
        mock_user.is_premium = False
        mock_user.premium_expires_at = None

        # Mock database session
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=mock_user)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.payment_service.get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Act
            result = await payment_service.check_premium_status(user_id)

            # Assert
            assert result["is_premium"] is False
            assert result["expires_at"] is None
            assert "remaining_days" in result
