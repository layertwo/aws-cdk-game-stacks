#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from lib.config.minecraft import MINECRAFT_PROPS
from lib.stacks.minecraft_stack import MinecraftStack

app = App()
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT", "000000000000"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ca-central-1"),
)

minecraft_stack = MinecraftStack(scope=app, props=MINECRAFT_PROPS, env=env)
app.synth()
