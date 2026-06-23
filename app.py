#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from cdk.config.minecraft import MINECRAFT_PROPS
from cdk.stacks.github_oidc_stack import GithubOidcStack
from cdk.stacks.minecraft_stack import MinecraftStack

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
app.synth()
