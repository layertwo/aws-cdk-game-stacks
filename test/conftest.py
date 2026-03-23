import pytest

from lib.config import GamePort, GameProperties, PortType, ServiceType


@pytest.fixture
def game_properties() -> GameProperties:
    return GameProperties(
        name="TestGame",
        container_image="foobar-container/latest",
        container_path="/data",
        ports=[
            GamePort(port_type=PortType.TCP, number=80),
            GamePort(port_type=PortType.UDP, number=53),
        ],
        environment={
            "FOO": "BAR",
        },
        auto_start=True,
        start_time="0 23 * * FRI",
        stop_time="0 6 * * MON",
        domain_name="example.com",
        hosted_zone_id="Z00000000000000000000",
        instance_type="t4g.large",
        instance_connect=True,
    )


@pytest.fixture
def fargate_game_properties() -> GameProperties:
    return GameProperties(
        name="TestGame",
        container_image="foobar-container/latest",
        container_path="/data",
        service_type=ServiceType.FARGATE,
        ports=[
            GamePort(port_type=PortType.TCP, number=80),
        ],
        environment={
            "FOO": "BAR",
        },
        domain_name="example.com",
        hosted_zone_id="Z00000000000000000000",
    )


@pytest.fixture
def webhook_game_properties() -> GameProperties:
    return GameProperties(
        name="TestGame",
        container_image="foobar-container/latest",
        container_path="/data",
        service_type=ServiceType.FARGATE,
        ports=[GamePort(port_type=PortType.TCP, number=80)],
        environment={"FOO": "BAR"},
        domain_name="example.com",
        hosted_zone_id="Z00000000000000000000",
        webhook_enabled=True,
    )


@pytest.fixture
def watchdog_game_properties() -> GameProperties:
    return GameProperties(
        name="TestGame",
        container_image="foobar-container/latest",
        container_path="/data",
        service_type=ServiceType.FARGATE,
        ports=[GamePort(port_type=PortType.TCP, number=80)],
        environment={"FOO": "BAR"},
        domain_name="example.com",
        hosted_zone_id="Z00000000000000000000",
        cloudwatch_metric_namespace="Minecraft",
        cloudwatch_player_count_metric="players_online",
        idle_shutdown_minutes=20,
    )
