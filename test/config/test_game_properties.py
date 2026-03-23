import pytest

from lib.config import GameProperties

BASE_KWARGS = dict(
    name="TestGame",
    container_image="img:latest",
    container_path="/data",
)


def test_default_webhook_fields():
    props = GameProperties(**BASE_KWARGS)
    assert props.webhook_enabled is False
    assert props.idle_shutdown_minutes == 20
    assert props.cloudwatch_metric_namespace is None
    assert props.cloudwatch_player_count_metric is None


def test_both_cw_fields_set_is_valid():
    props = GameProperties(
        **BASE_KWARGS,
        cloudwatch_metric_namespace="Minecraft",
        cloudwatch_player_count_metric="players_online",
    )
    assert props.cloudwatch_metric_namespace == "Minecraft"


def test_only_namespace_raises():
    with pytest.raises(ValueError, match="cloudwatch"):
        GameProperties(**BASE_KWARGS, cloudwatch_metric_namespace="Minecraft")


def test_only_metric_raises():
    with pytest.raises(ValueError, match="cloudwatch"):
        GameProperties(**BASE_KWARGS, cloudwatch_player_count_metric="players_online")


def test_idle_shutdown_minutes_must_be_multiple_of_5():
    with pytest.raises(ValueError, match="idle_shutdown_minutes"):
        GameProperties(**BASE_KWARGS, idle_shutdown_minutes=22)


def test_idle_shutdown_minutes_must_be_positive():
    with pytest.raises(ValueError, match="idle_shutdown_minutes"):
        GameProperties(**BASE_KWARGS, idle_shutdown_minutes=0)


def test_idle_shutdown_minutes_valid():
    props = GameProperties(**BASE_KWARGS, idle_shutdown_minutes=15)
    assert props.idle_shutdown_minutes == 15
