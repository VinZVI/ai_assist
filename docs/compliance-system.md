# Compliance System Documentation

## Overview

The compliance system implements a simplified consent and age verification process for users accessing the AI assistant bot. This system ensures legal compliance by requiring users to confirm their age (18+) and accept terms of service before using the bot.

## System Components

### 1. Compliance Package Structure

```
app/
├── compliance/
│   ├── __init__.py
│   ├── age_verification.py      # Age verification functionality
│   ├── consent_manager.py       # Consent management
│   └── legal_texts.py          # Legal texts and messages
├── handlers/
│   └── onboarding.py           # Onboarding handler
├── keyboards/
│   └── onboarding_keyboards.py # Onboarding keyboards
├── middleware/
│   └── verification_middleware.py # Verification middleware
```

### 2. Key Modules

#### Age Verification (`app/compliance/age_verification.py`)

Handles age verification processes for users:
- Verifies if a user has confirmed they are 18+
- Updates user verification status in the database
- Checks if age verification is required

#### Consent Manager (`app/compliance/consent_manager.py`)

Manages the user consent process:
- Handles different types of consent (terms, privacy, guidelines)
- Processes user responses to consent requests
- Checks verification status
- Determines if onboarding is required

#### Legal Texts (`app/compliance/legal_texts.py`)

Contains all legal texts and messages displayed to users:
- Welcome message
- Consent agreement text
- Success and rejection messages
- Bot information text

#### Onboarding Handler (`app/handlers/onboarding.py`)

Handles the user onboarding flow:
- Processes `/start` command
- Handles onboarding callbacks
- Manages consent callbacks
- Controls the onboarding state machine

#### Onboarding Keyboards (`app/keyboards/onboarding_keyboards.py`)

Provides interactive keyboards for the onboarding process:
- Welcome keyboard
- Consent keyboard
- Completion keyboard
- Information keyboard

#### Verification Middleware (`app/middleware/verification_middleware.py`)

Middleware that checks user verification status:
- Blocks unverified users from accessing restricted features
- Allows certain commands without verification
- Handles unverified user responses

## Database Changes

### New User Fields

The following fields were added to the User model:

| Field | Type | Description |
|-------|------|-------------|
| `age_verified` | Boolean | Whether the user has confirmed they are 18+ |
| `terms_accepted` | Boolean | Whether the user has accepted terms of service |
| `privacy_policy_accepted` | Boolean | Whether the user has accepted privacy policy |
| `community_guidelines_accepted` | Boolean | Whether the user has accepted community guidelines |
| `consent_timestamp` | DateTime | When consent was given |
| `consent_ip_address` | String(45) | IP address when consent was given |
| `terms_version` | String(10) | Version of terms accepted |
| `privacy_version` | String(10) | Version of privacy policy accepted |
| `guidelines_version` | String(10) | Version of guidelines accepted |
| `verification_status` | Enum | Status of user verification (pending, verified, rejected, expired) |

### New Property

- `is_fully_verified`: Computed property that returns True if all consents are accepted and verification status is 'verified'

## Configuration

### Environment Variables

The following environment variables were added:

```bash
# Compliance and Verification Settings
TERMS_VERSION=1.0
PRIVACY_VERSION=1.0
GUIDELINES_VERSION=1.0
REQUIRE_AGE_VERIFICATION=true
VERIFICATION_TIMEOUT_HOURS=24

# Legal Documents URLs
TERMS_URL=https://telegra.ph/Terms-of-Service-and-Privacy-Policy--AI-Assist-06-14
GUIDELINES_URL=https://telegra.ph/AI-Assist-Community-Guidelines-06-14
```

## Onboarding Flow

1. User sends `/start` command
2. System checks if onboarding is required
3. If already verified, shows completion message
4. If not verified, shows welcome message with registration button
5. User clicks "Start Registration"
6. System shows consent form with links to legal documents
7. User accepts or rejects consent
8. If accepted, user is marked as verified and completion message is shown
9. If rejected, user is informed they cannot use the bot

## Middleware Protection

The verification middleware protects the bot by:
- Allowing unrestricted access to `/start`, `/help`, and `/support` commands
- Blocking access to all other commands for unverified users
- Allowing full access for verified users

## Testing

Unit tests cover:
- New user onboarding requirement
- Consent acceptance flow
- Consent rejection flow
- Verification middleware behavior for verified and unverified users
- Allowed command access for unverified users

## Migration

A database migration was created to add the new fields to the users table:
- `alembic/versions/add_user_verification_and_consent_fields.py`

## Implementation Status

✅ **Completed Components:**
- Database model updates
- Compliance package implementation
- Onboarding handler
- Verification middleware
- Legal texts
- Keyboards
- Configuration updates
- Database migration
- Unit tests

⏳ **Pending Components:**
- Integration with main application
- End-to-end testing
- Documentation updates