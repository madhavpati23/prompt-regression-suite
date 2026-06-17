import json

import pytest

from prompt_regression.models import ClaudeModel, HttpModel, MockModel, get_model


def test_render_body_escapes_prompt_safely():
    body = HttpModel.render_body('{"prompt": {PROMPT}}', 'say "hi"\nthen stop')
    parsed = json.loads(body)                      # must be valid JSON
    assert parsed == {"prompt": 'say "hi"\nthen stop'}


def test_render_body_custom_template():
    tmpl = '{"messages": [{"role": "user", "content": {PROMPT}}]}'
    parsed = json.loads(HttpModel.render_body(tmpl, "hello"))
    assert parsed["messages"][0]["content"] == "hello"


def test_extract_dotted_path_openai_shape():
    raw = json.dumps({"choices": [{"message": {"content": "Paris"}}]})
    assert HttpModel.extract(raw, "choices.0.message.content") == "Paris"


def test_extract_empty_path_returns_raw_text():
    assert HttpModel.extract("  plain text reply  ", "") == "plain text reply"


def test_extract_non_string_is_json_encoded():
    raw = json.dumps({"answer": {"label": "positive"}})
    assert HttpModel.extract(raw, "answer") == '{"label": "positive"}'


def test_name_is_host_based():
    m = HttpModel(url="https://api.example.com/v1/chat")
    assert m.name == "http:api.example.com"


def test_get_model_precedence_http_wins(monkeypatch):
    monkeypatch.setenv("PRS_HTTP_URL", "https://api.example.com/chat")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")   # should be ignored
    assert isinstance(get_model(), HttpModel)


def test_get_model_falls_back_to_mock(monkeypatch):
    monkeypatch.delenv("PRS_HTTP_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(get_model(), MockModel)
