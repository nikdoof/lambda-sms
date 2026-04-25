import logging

import boto3
import pytest
from moto import mock_aws

from smsbot import config


@pytest.fixture(autouse=True)
def _reset_cache():
    config.load.cache_clear()
    yield
    config.load.cache_clear()


@pytest.fixture
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.delenv("SSM_PATH_PREFIX", raising=False)


def _seed_params(client, prefix: str, *, subscribers: str = "111,222"):
    client.put_parameter(Name=f"{prefix}/twilio/auth_token", Value="t-secret", Type="SecureString")
    client.put_parameter(Name=f"{prefix}/telegram/bot_token", Value="b-secret", Type="SecureString")
    client.put_parameter(Name=f"{prefix}/telegram/subscribers", Value=subscribers, Type="String")


@mock_aws
def test_load_returns_populated_config(aws_env):
    ssm = boto3.client("ssm")
    _seed_params(ssm, "/smsbot")

    cfg = config.load()

    assert cfg.twilio_auth_token == "t-secret"
    assert cfg.telegram_bot_token == "b-secret"
    assert cfg.subscribers == [111, 222]


@mock_aws
def test_load_respects_path_prefix(aws_env, monkeypatch):
    monkeypatch.setenv("SSM_PATH_PREFIX", "/custom/smsbot")
    ssm = boto3.client("ssm")
    _seed_params(ssm, "/custom/smsbot", subscribers="42")

    cfg = config.load()

    assert cfg.subscribers == [42]


@mock_aws
def test_load_strips_trailing_slash_in_prefix(aws_env, monkeypatch):
    monkeypatch.setenv("SSM_PATH_PREFIX", "/smsbot/")
    ssm = boto3.client("ssm")
    _seed_params(ssm, "/smsbot")

    cfg = config.load()

    assert cfg.subscribers == [111, 222]


@mock_aws
def test_load_raises_on_missing_parameter(aws_env):
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name="/smsbot/telegram/subscribers", Value="111", Type="String")
    # twilio/auth_token and telegram/bot_token deliberately absent

    with pytest.raises(RuntimeError, match="Missing required SSM parameter"):
        config.load()


@mock_aws
def test_load_rejects_placeholder_values(aws_env):
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name="/smsbot/twilio/auth_token", Value="REPLACE_ME", Type="SecureString")
    ssm.put_parameter(Name="/smsbot/telegram/bot_token", Value="real-token", Type="SecureString")
    ssm.put_parameter(Name="/smsbot/telegram/subscribers", Value="111", Type="String")

    with pytest.raises(RuntimeError, match="placeholder values"):
        config.load()


@mock_aws
def test_load_warns_on_empty_subscribers(aws_env, caplog):
    ssm = boto3.client("ssm")
    _seed_params(ssm, "/smsbot", subscribers=" , ")

    with caplog.at_level(logging.WARNING, logger="smsbot.config"):
        cfg = config.load()

    assert cfg.subscribers == []
    assert any("No Telegram subscribers" in r.message for r in caplog.records)
