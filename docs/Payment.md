# Telegram Stars Payment Integration

## Overview

This document describes the implementation of Telegram Stars payment integration for premium subscriptions in the AI-Companion bot. The integration allows users to purchase premium access using Telegram Stars, a native payment system in Telegram.

## Features

1. **Telegram Stars Integration**: Full integration with Telegram's native payment system
2. **Premium Subscription Plans**: Multiple subscription options with different durations
3. **Payment Tracking**: Database storage of all payment transactions
4. **Premium Status Management**: Automatic activation and expiration of premium subscriptions
5. **Multi-language Support**: Payment messages in both Russian and English

## Architecture

### Components

1. **Payment Model**: Database model for storing payment information
2. **Payment Service**: Business logic for handling payments and premium subscriptions
3. **Callback Handlers**: Integration with Telegram's callback system for payment initiation
4. **Message Handlers**: Processing of successful payments
5. **Configuration**: Payment-related settings and parameters

### Data Flow

1. User selects premium plan in the bot interface
2. Bot creates an invoice using Telegram's `send_invoice` method
3. User completes payment in Telegram
4. Telegram sends a `SuccessfulPayment` event to the bot
5. Bot processes the payment and activates premium subscription
6. Payment information is stored in the database

## Implementation Details

### Payment Model

The `Payment` model stores information about all transactions:

- `id`: Internal payment ID
- `user_id`: Reference to the user who made the payment
- `amount`: Amount in Telegram Stars
- `currency`: Currency code (XTR for Telegram Stars)
- `payment_provider`: Payment provider (telegram_stars)
- `payment_id`: Telegram's payment charge ID
- `status`: Payment status (completed, refunded, failed)
- `created_at`: Timestamp of payment creation

### Payment Service

The `TelegramStarsPaymentService` handles all payment-related operations:

- Creating invoices
- Processing successful payments
- Activating/deactivating premium subscriptions
- Checking premium status

### Premium Plans

The bot offers three premium subscription plans:

1. **Monthly**: 100 Telegram Stars for 30 days
2. **Quarterly**: 250 Telegram Stars for 90 days (15% discount)
3. **Yearly**: 800 Telegram Stars for 365 days (30% discount)

### Configuration

Payment settings can be configured through environment variables:

- `PAYMENT_ENABLED`: Enable/disable payment functionality
- `PAYMENT_PROVIDER`: Payment provider (telegram_stars)
- `PAYMENT_TEST_MODE`: Enable test mode

## Security Considerations

1. **Payload Validation**: All payment payloads are validated to prevent tampering
2. **User Verification**: Payments are linked to specific users to prevent fraud
3. **Error Handling**: Comprehensive error handling to prevent inconsistent states
4. **Logging**: Detailed logging of all payment operations for audit purposes

## Testing

Unit tests cover all aspects of the payment system:

- Invoice creation
- Payment processing
- Premium activation/deactivation
- Status checking
- Error handling

## Future Improvements

1. **Refund Handling**: Process refund events from Telegram
2. **Subscription Management**: Allow users to manage their subscriptions
3. **Analytics Dashboard**: Admin interface for viewing payment statistics
4. **Promotional Codes**: Support for discount codes
5. **Gift Subscriptions**: Allow users to gift premium subscriptions to others

## API Reference

### TelegramStarsPaymentService

#### Methods

- `create_invoice(user_id, amount, description, duration_days)`: Create a payment invoice
- `handle_successful_payment(payment, user_telegram_id)`: Process a successful payment
- `activate_premium(user_id, duration_days)`: Activate premium subscription
- `deactivate_premium(user_id)`: Deactivate premium subscription
- `check_premium_status(user_id)`: Check premium subscription status

## Troubleshooting

### Common Issues

1. **Payment Creation Failed**: Check Telegram bot token and payment configuration
2. **Payment Not Processed**: Verify webhook configuration and payment handler registration
3. **Premium Not Activated**: Check database connection and user ID mapping

### Logs

All payment operations are logged with the prefix `payment.` in the log system:

- `payment.invoice_created`: Invoice successfully created
- `payment.invoice_creation_error`: Error creating invoice
- `payment.payment_processed`: Payment successfully processed
- `payment.payment_handling_error`: Error processing payment
- `payment.premium_activated`: Premium subscription activated
- `payment.premium_activation_failed`: Failed to activate premium subscription
- `payment.premium_activation_error`: Error activating premium subscription