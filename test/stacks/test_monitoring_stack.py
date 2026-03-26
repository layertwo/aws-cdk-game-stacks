import pytest
from aws_cdk import App, Environment
from aws_cdk.assertions import Template

from lib.stacks.minecraft_stack import MinecraftStack
from lib.stacks.monitoring_stack import MinecraftMonitoringStack
from lib.config.minecraft import MINECRAFT_PROPS


@pytest.fixture
def monitoring_stack():
    app = App()
    env = Environment(account="000000000000", region="ca-central-1")
    minecraft_stack = MinecraftStack(scope=app, props=MINECRAFT_PROPS, env=env)
    return MinecraftMonitoringStack(scope=app, minecraft_stack=minecraft_stack, env=env)


def test_dashboard_created(monitoring_stack):
    template = Template.from_stack(monitoring_stack)
    template.resource_count_is("AWS::CloudWatch::Dashboard", 1)


def test_depends_on_minecraft_stack():
    app = App()
    env = Environment(account="000000000000", region="ca-central-1")
    minecraft_stack = MinecraftStack(scope=app, props=MINECRAFT_PROPS, env=env)
    mon_stack = MinecraftMonitoringStack(scope=app, minecraft_stack=minecraft_stack, env=env)
    assert minecraft_stack in mon_stack.dependencies
