# Fix for Database Context JSON Serialization Issue

## Problem Description

The Telegram bot was experiencing errors when trying to backup conversation context to Redis after restoring context from the database:

```
❌ 19:37:29 | ERROR    | conversation_persistence:203 | Failed to backup to Redis for user 1: Object of type ConversationMessage is not JSON serializable
```

## Root Cause

The issue occurred in the [get_conversation_context](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service.py#L84-L147) function in [app/services/conversation_service.py](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service.py). When retrieving conversation context from the database, the function was directly assigning [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects and datetime objects to the context dictionary without proper JSON serialization:

```python
context = {
    "history": history,  # Direct assignment of ConversationMessage objects
    "last_interaction": history[-1].timestamp if history else None,  # Direct assignment of datetime object
    # ... other fields
}
```

When this context was later passed to the conversation persistence layer for backup to Redis, the JSON serialization failed because:
1. [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects are not JSON serializable
2. datetime objects are not JSON serializable

## Solution

The fix involved properly converting [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects and datetime objects to JSON-serializable formats before adding them to the context dictionary.

### 1. Serialize ConversationMessage Objects

Convert each [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) object to a dictionary with proper JSON-serializable fields:

```python
# Преобразуем ConversationMessage объекты в словари для сериализации
serialized_history = [
    {
        "role": msg.role,
        "content": msg.content,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
    }
    for msg in history
]
```

### 2. Serialize datetime Objects

Convert datetime objects to ISO format strings:

```python
"last_interaction": history[-1].timestamp.isoformat() if history and history[-1].timestamp else None,
```

## Files Modified

1. [app/services/conversation_service.py](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service.py) - Fixed JSON serialization issue in the [get_conversation_context](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service.py#L84-L147) function
2. [tests/test_database_context_serialization.py](file:///c:/Users/User/PycharmProjects/ai_assist/tests/test_database_context_serialization.py) - Added tests to verify the fix

## Verification

Tests were created and run to verify that:
1. Conversation context retrieved from the database can be properly serialized to JSON
2. [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects can be properly converted to JSON-serializable dictionaries
3. datetime objects are properly converted to ISO format strings

All tests pass successfully, confirming that the fix resolves the JSON serialization issue when backing up conversation context to Redis after restoring from the database.

## Impact

This fix ensures that:
1. Conversation context can be properly restored from the database and backed up to Redis without errors
2. The bot can maintain conversation context across restarts
3. Data integrity is maintained during the persistence process
4. Users experience consistent behavior when interacting with the bot after restarts