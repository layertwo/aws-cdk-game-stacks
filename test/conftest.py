import pytest

from lib.config import GamePort, GameProperties, PortType


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
        start_time="0 23 * * FRI",  # Friday 3PM PST
        stop_time="0 6 * * MON",  # Sunday 10PM PST,
        domain_name="example.com",
        hosted_zone_id="Z00000000000000000000",
        instance_type="t4g.large",
        instance_connect=True,
    )
