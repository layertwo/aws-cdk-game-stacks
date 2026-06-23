from cdk.config import GameProperties

BASE_KWARGS = dict(
    name="TestGame",
    container_image="img:latest",
    container_path="/data",
)


def test_default_webhook_fields():
    props = GameProperties(**BASE_KWARGS)
    assert props.webhook_enabled is False
    assert props.idle_shutdown_minutes == 20


def test_idle_shutdown_minutes_valid():
    props = GameProperties(**BASE_KWARGS, idle_shutdown_minutes=15)
    assert props.idle_shutdown_minutes == 15
