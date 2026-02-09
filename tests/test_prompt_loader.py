# tests/test_prompt_loader.py
import pytest
from services.prompt_loader import PromptLoader


class TestPromptLoader:
    def test_get_prompt_returns_formatted_text(self):
        loader = PromptLoader("config/prompts.yaml")
        result = loader.get_prompt("polish", "work_email", "Hello world")
        assert "Hello world" in result
        assert "正式商务语气" in result
    
    def test_get_prompt_by_numbers_returns_formatted_text(self):
        loader = PromptLoader("config/prompts.yaml")
        result = loader.get_prompt_by_numbers(1, 1, "Hello world")
        assert "Hello world" in result
        assert "正式商务语气" in result

    def test_get_prompt_unknown_button_raises(self):
        loader = PromptLoader("config/prompts.yaml")
        with pytest.raises(KeyError):
            loader.get_prompt("unknown_button", "work_email", "text")

    def test_get_prompt_unknown_role_raises(self):
        loader = PromptLoader("config/prompts.yaml")
        with pytest.raises(KeyError):
            loader.get_prompt("polish", "unknown_role", "text")
    
    def test_get_prompt_by_numbers_out_of_range_raises(self):
        loader = PromptLoader("config/prompts.yaml")
        with pytest.raises(ValueError):
            loader.get_prompt_by_numbers(999, 1, "text")

    def test_list_roles(self):
        loader = PromptLoader("config/prompts.yaml")
        roles = loader.list_roles()
        assert "work_email" in roles
        assert "social_chat" in roles

    def test_list_buttons(self):
        loader = PromptLoader("config/prompts.yaml")
        buttons = loader.list_buttons()
        assert "polish" in buttons
        assert "expand" in buttons
