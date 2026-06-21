import pytest

from prompt_regression.models import HttpAgentModel, HttpModel, _assert_safe_url


def test_non_http_schemes_are_rejected():
    for bad in ["file:///etc/passwd", "ftp://host/x", "gopher://host", "data:text/plain,hi"]:
        with pytest.raises(ValueError):
            _assert_safe_url(bad, block_private=False)


def test_constructor_rejects_file_scheme():
    with pytest.raises(ValueError):
        HttpModel(url="file:///etc/passwd")


def test_http_agent_model_constructor_rejects_file_scheme():
    with pytest.raises(ValueError):
        HttpAgentModel(url="file:///etc/passwd")


def test_http_agent_model_name_derived_from_host():
    m = HttpAgentModel(url="https://my-agent.example.com/run")
    assert m.name == "agent:my-agent.example.com"


def test_ssrf_block_rejects_loopback_and_metadata():
    for bad in ["http://127.0.0.1/x", "http://localhost/x",
                "http://169.254.169.254/latest/meta-data", "http://[::1]/x"]:
        with pytest.raises(ValueError):
            _assert_safe_url(bad, block_private=True)


def test_private_addresses_allowed_when_not_blocked():
    # local internal-endpoint testing is legitimate when SSRF blocking is off
    _assert_safe_url("http://127.0.0.1:8000/chat", block_private=False)
    _assert_safe_url("http://10.0.0.5/api", block_private=False)


def test_public_address_allowed_even_when_blocked():
    _assert_safe_url("http://8.8.8.8/", block_private=True)        # public IP, no DNS
