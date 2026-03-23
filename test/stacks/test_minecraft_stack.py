from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template

from lib.config import GameProperties
from lib.stacks.minecraft_stack import MinecraftStack


def test_game_stack_synth(game_properties: GameProperties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=game_properties, env=env)

    Template.from_stack(stack)
    assert True


def test_minecraft_fargate_no_asg(fargate_game_properties: GameProperties):
    """Fargate stacks must not synthesize any AutoScaling resources."""
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=fargate_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 0)


def test_minecraft_fargate_single_service(fargate_game_properties: GameProperties):
    """Only the Minecraft Fargate service should exist — no Traefik service."""
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=fargate_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::ECS::Service", 1)


def test_minecraft_fargate_service_public_ip_and_sg(fargate_game_properties: GameProperties):
    """Fargate service must have AssignPublicIp enabled and at least one security group."""
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=fargate_game_properties, env=env)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::Service",
        {
            "LaunchType": "FARGATE",
            "NetworkConfiguration": {
                "AwsvpcConfiguration": {
                    "AssignPublicIp": "ENABLED",
                    "SecurityGroups": Match.array_with([Match.object_like({"Fn::GetAtt": Match.any_value()})]),
                }
            },
        },
    )
