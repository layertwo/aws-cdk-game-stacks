import pytest
from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template

from lib.stacks.minecraft_stack import MinecraftStack


@pytest.fixture(scope="session")
def fargate_template(fargate_game_properties) -> Template:
    """Fargate stacks must not synthesize any AutoScaling resources."""
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=fargate_game_properties, env=env)
    return Template.from_stack(stack)


@pytest.fixture(scope="session")
def webhook_template(webhook_game_properties) -> Template:
    """Fargate stacks must not synthesize any AutoScaling resources."""
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = MinecraftStack(scope=app, props=webhook_game_properties, env=env)
    return Template.from_stack(stack)


def test_minecraft_fargate_no_asg(fargate_template):
    fargate_template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 0)


def test_minecraft_fargate_single_service(fargate_template):
    fargate_template.resource_count_is("AWS::ECS::Service", 1)


def test_minecraft_fargate_service_public_ip_and_sg(fargate_template):
    """Fargate service must have AssignPublicIp enabled and at least one security group."""
    fargate_template.has_resource_properties(
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


def test_webhook_not_created_when_disabled(fargate_template):
    fargate_template.resource_count_is("AWS::Lambda::Url", 0)


def test_webhook_lambda_created(webhook_template):
    webhook_template.has_resource_properties(
        "AWS::Lambda::Function",
        {"FunctionName": "TestGameWebhookLambda"},
    )


def test_webhook_function_url_created(webhook_template):
    webhook_template.resource_count_is("AWS::Lambda::Url", 1)
    webhook_template.has_resource_properties(
        "AWS::Lambda::Url",
        {"AuthType": "NONE"},
    )


def test_webhook_url_stored_in_ssm(webhook_template):
    webhook_template.has_resource_properties(
        "AWS::SSM::Parameter",
        {"Name": "/testgame/webhook-url", "Type": "String"},
    )


def test_watchdog_alarm_created(webhook_template):
    webhook_template.resource_count_is("AWS::CloudWatch::Alarm", 1)
    webhook_template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "Namespace": "Minecraft",
            "MetricName": "OnlinePlayers",
            "Statistic": "Maximum",
            "Period": 60,
            "EvaluationPeriods": 20,
            "DatapointsToAlarm": 20,
            "Threshold": 0,
            "TreatMissingData": "breaching",
            "Dimensions": Match.array_with([{"Name": "Server", "Value": "testgame"}]),
        },
    )


def test_watchdog_sns_topic_created(webhook_template):
    webhook_template.resource_count_is("AWS::SNS::Topic", 1)


def test_watchdog_task_count_lambda_created(webhook_template):
    webhook_template.has_resource_properties(
        "AWS::Lambda::Function",
        {"FunctionName": "TestGameTaskCountLambda"},
    )
