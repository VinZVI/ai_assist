# Fix for ConversationMessage JSON Serialization Issue

## Problem Description

The Telegram bot was experiencing errors when trying to backup conversation context to Redis:

```
❌ 19:31:35 | ERROR    | conversation_persistence:203 | Failed to backup to Redis for user 1: Object of type ConversationMessage is not JSON serializable
```

## Root Cause

The issue was in the [ConversationService](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service_new.py#L38-L418) class in [app/services/conversation_service_new.py](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service_new.py). When creating the context dictionary for serialization, the code was directly assigning `ConversationMessage` objects to the `history` field:

```python
context_dict["history"] = context.get_combined_history()
```

The [get_combined_history()](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L118-L131) method returns a list of [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects, which are not JSON serializable. When the conversation persistence layer tried to serialize this data to store in Redis, it failed with the "Object of type ConversationMessage is not JSON serializable" error.

## Solution

The fix involved properly converting the [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects to dictionaries before adding them to the context dictionary. This was done in two places in the [ConversationService](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service_new.py#L38-L418) class:

1. In the [get_conversation_context](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service_new.py#L141-L182) method (line 159)
2. In the [save_conversation_with_cache](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service_new.py#L186-L299) method (line 273)

The fix converts each [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) object to a dictionary with the proper JSON-serializable fields:

```python
context_dict["history"] = [
    {
        "role": msg.role,
        "content": msg.content,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
    }
    for msg in context.get_combined_history()
]
```

## Files Modified

1. [app/services/conversation_service_new.py](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/conversation_service_new.py) - Fixed JSON serialization issue in two methods
2. [tests/test_conversation_serialization.py](file:///c:/Users/User/PycharmProjects/ai_assist/tests/test_conversation_serialization.py) - Added tests to verify the fix
3. [tests/test_conversation_service_serialization.py](file:///c:/Users/User/PycharmProjects/ai_assist/tests/test_conversation_service_serialization.py) - Added comprehensive tests for the service

## Verification

Tests were created and run to verify that:
1. [ConversationMessage](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L29-L34) objects can be properly serialized to JSON
2. [UserAIConversationContext](file:///c:/Users/User/PycharmProjects/ai_assist/app/services/ai_providers/base.py#L37-L179) can be properly serialized to JSON with the history field
3. The fixed code in the service properly handles serialization

All tests pass successfully, confirming that the fix resolves the JSON serialization issue.