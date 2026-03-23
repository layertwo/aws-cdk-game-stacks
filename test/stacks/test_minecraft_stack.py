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
            "CapacityProviderStrategy": Match.array_with(
                [Match.object_like({"CapacityProvider": "FARGATE_SPOT"})]
            ),
            "NetworkConfiguration": {
                "AwsvpcConfiguration": {
                    "AssignPublicIp": "ENABLED",
                    "SecurityGroups": Match.array_with(
                        [Match.object_like({"Fn::GetAtt": Match.any_value()})]
                    ),
                }
            },
        },
    )


def test_webhook_lambda_created(webhook_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=webhook_game_properties, env=env)
    template = Template.from_stack(stack)

    # Lambda function named TestGameWebhookLambda
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"FunctionName": "TestGameWebhookLambda"},
    )


def test_webhook_function_url_created(webhook_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=webhook_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::Url", 1)
    template.has_resource_properties(
        "AWS::Lambda::Url",
        {"AuthType": "NONE"},
    )


def test_webhook_url_stored_in_ssm(webhook_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=webhook_game_properties, env=env)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::SSM::Parameter",
        {"Name": "/testgame/webhook-url", "Type": "String"},
    )


def test_webhook_not_created_when_disabled(fargate_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=fargate_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::Url", 0)


def test_watchdog_alarm_created(watchdog_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=watchdog_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CloudWatch::Alarm", 1)
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "Namespace": "Minecraft",
            "MetricName": "players_online",
            "Statistic": "Maximum",
            "Period": 300,
            "EvaluationPeriods": 4,
            "DatapointsToAlarm": 4,
            "Threshold": 0,
            "TreatMissingData": "breaching",
        },
    )


def test_watchdog_sns_topic_created(watchdog_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=watchdog_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)


def test_watchdog_task_count_lambda_created(watchdog_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=watchdog_game_properties, env=env)
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"FunctionName": "TestGameTaskCountLambda"},
    )


def test_watchdog_not_created_when_no_cw_fields(fargate_game_properties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=fargate_game_properties, env=env)
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::CloudWatch::Alarm", 0)
    template.resource_count_is("AWS::SNS::Topic", 0)
