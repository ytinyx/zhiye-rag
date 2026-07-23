"""RAG behavior is tested without paid APIs; remote calls are opt-in."""
import os
from unittest.mock import Mock

import pytest

from src.llm.rag import build_prompt, format_context, generate_answer


def test_format_context_deduplicates_and_limits_length():
    context = format_context([
        {"content": "first passage"}, {"content": "first passage"},
        {"content": ""}, {"content": "second passage"}, {"content": "x" * 100},
    ], max_chars=40)
    assert context == "first passage\n\nsecond passage"
    assert len(context) <= 40


def test_build_prompt_keeps_question_and_context_in_their_sections():
    prompt = build_prompt(question="What is RAG?", context="Retrieved text.")
    assert "[上下文]\nRetrieved text." in prompt
    assert "[问题]\n问:What is RAG?" in prompt


def test_generate_answer_uses_retrieved_context():
    llm = Mock()
    llm.generate.return_value = {
        "content": "A supported answer.", "model": "fake-model",
        "token_used": {"total": 8, "prompt": 5, "completion": 3},
    }
    result = generate_answer(llm, "What is RAG?", [{"content": "Retrieved text."}],
                             temperature=0.2, max_token=100)
    assert result["answer"] == "A supported answer."
    assert result["context"] == "Retrieved text."
    assert result["question"] == "What is RAG?"
    llm.generate.assert_called_once_with(
        [{"role": "user", "content": build_prompt("What is RAG?", "Retrieved text.")}],
        temperature=0.2, max_token=100,
    )


def test_generate_answer_without_results_does_not_call_llm():
    llm = Mock()
    result = generate_answer(llm, "Unknown question", [])
    assert result["answer"] == "我不知道"
    assert result["token_used"]["total"] == 0
    llm.generate.assert_not_called()


@pytest.mark.external_api
@pytest.mark.parametrize("prefix, default_model, default_url", [
    ("ZHIPU", "glm-4-flash", "https://open.bigmodel.cn/api/paas/v4/"),
    ("DASHSCOPE", "qwen-plus", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
])
def test_remote_llm(prefix, default_model, default_url):
    api_key = os.getenv(f"{prefix}_API_KEY")
    if not api_key:
        pytest.skip(f"Set {prefix}_API_KEY explicitly to run this test")
    from src.llm.llm import LLM

    llm = LLM(os.getenv(f"{prefix}_MODEL", default_model), api_key,
              os.getenv(f"{prefix}_BASE_URL", default_url))
    result = llm.generate([{"role": "user", "content": "请回复：测试成功"}], max_token=30)
    assert result["content"].strip()
    assert result["token_used"]["total"] > 0
