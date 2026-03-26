#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from lib.config.minecraft import MINECRAFT_PROPS
from lib.stacks.github_oidc_stack import GithubOidcStack
from lib.stacks.minecraft_stack import MinecraftStack
from lib.stacks.monitoring_stack import MinecraftMonitoringStack

app = App()
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT", "000000000000"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ca-central-1"),
)

github_oidc_stack = GithubOidcStack(
    scope=app,
    stack_id="GithubOidcStack",
    env=env,
    github_org="layertwo",
    github_repo="aws-cdk-game-stacks",
)
minecraft_stack = MinecraftStack(scope=app, props=MINECRAFT_PROPS, env=env)
MinecraftMonitoringStack(scope=app, minecraft_stack=minecraft_stack, env=env)
app.synth()
