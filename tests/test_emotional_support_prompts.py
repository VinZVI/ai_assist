"""
Tests for emotional support AI prompts
"""

import pytest

from app.lexicon.ai_prompts import (
    create_crisis_intervention_prompt,
    create_mature_content_prompt,
    create_system_message,
)


@pytest.mark.asyncio
async def test_create_system_message_russian() -> None:
    """Test creating system message in Russian."""
    message = create_system_message("ru")
    assert "эмоциональную поддержку" in message
    assert "психологический комфорт" in message
    assert "контент 18+" in message


@pytest.mark.asyncio
async def test_create_system_message_english() -> None:
    """Test creating system message in English."""
    message = create_system_message("en")
    assert "emotional support" in message
    assert "psychological comfort" in message
    assert "18+ content" in message


def test_create_system_message_default_language() -> None:
    """Test creating system message with default language."""
    message = create_system_message()
    assert "emotional support" in message
    assert "psychological comfort" in message
    assert "18+ content" in message


def test_create_crisis_intervention_prompt_russian() -> None:
    """Test creating crisis intervention prompt in Russian."""
    prompt = create_crisis_intervention_prompt("ru")
    assert "кризисная ситуация" in prompt
    assert "немедленно обратиться за помощью" in prompt
    assert "доверие и поддержка" in prompt


def test_create_crisis_intervention_prompt_english() -> None:
    """Test creating crisis intervention prompt in English."""
    prompt = create_crisis_intervention_prompt("en")
    assert "crisis situation" in prompt
    assert "immediately seek help" in prompt
    assert "trust and support" in prompt


def test_create_mature_content_prompt_russian() -> None:
    """Test creating mature content prompt in Russian."""
    prompt = create_mature_content_prompt("ru")
    assert "взрослый контент" in prompt
    assert "уважение и конфиденциальность" in prompt
    assert "фактическую информацию" in prompt


def test_create_mature_content_prompt_english() -> None:
    """Test creating mature content prompt in English."""
    prompt = create_mature_content_prompt("en")
    assert "mature content" in prompt
    assert "respect and confidentiality" in prompt
    assert "factual information" in prompt


def test_prompts_contain_important_guidelines() -> None:
    """Test that prompts contain important guidelines for emotional support."""
    # Test Russian system message
    ru_message = create_system_message("ru")
    assert "профессиональная помощь" in ru_message
    assert "доверие и конфиденциальность" in ru_message
    assert "уважение и непредвзятость" in ru_message

    # Test English system message
    en_message = create_system_message("en")
    assert "professional help" in en_message
    assert "trust and confidentiality" in en_message
    assert "respect and non-judgmental" in en_message


def test_crisis_intervention_prompts_have_safety_focus() -> None:
    """Test that crisis intervention prompts focus on safety."""
    # Test Russian crisis prompt
    ru_prompt = create_crisis_intervention_prompt("ru")
    assert "немедленно обратиться за помощью" in ru_prompt
    assert "безопасность" in ru_prompt
    assert "профессиональная помощь" in ru_prompt

    # Test English crisis prompt
    en_prompt = create_crisis_intervention_prompt("en")
    assert "immediately seek help" in en_prompt
    assert "safety" in en_prompt
    assert "professional help" in en_prompt


def test_mature_content_prompts_have_appropriate_guidelines() -> None:
    """Test that mature content prompts have appropriate guidelines."""
    # Test Russian mature content prompt
    ru_prompt = create_mature_content_prompt("ru")
    assert "уважение и конфиденциальность" in ru_prompt
    assert "фактическую информацию" in ru_prompt
    assert "здоровое общение" in ru_prompt

    # Test English mature content prompt
    en_prompt = create_mature_content_prompt("en")
    assert "respect and confidentiality" in en_prompt
    assert "factual information" in en_prompt
    assert "healthy communication" in en_prompt
