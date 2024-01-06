import pytest
from aws_cdk import App
from aws_cdk.assertions import Template

from lib.config import GameProperties
from lib.stacks.game_stack import GameStack


@pytest.fixture
def game_properties() -> GameProperties:
    return GameProperties(
        name="TestGame",
        container_image="foobar-container/latest",
        container_path="/data",
        tcp_ports=[80],
        environment={
            "FOO": "BAR",
        },
        auto_start=True,
        start_time="0 23 * * FRI",  # Friday 3PM PST
        stop_time="0 6 * * MON",  # Sunday 10PM PST,
        domain_name="example.com",
        hosted_zone_id="Z09871391DBKPQ6VVS5KY",
        instance_type="t4g.large",
        instance_connect=False,
    )


def test_game_stack_synth(game_properties: GameProperties):
    app = App()
    stack = GameStack(scope=app, props=game_properties)

    Template.from_stack(stack)
    assert True
