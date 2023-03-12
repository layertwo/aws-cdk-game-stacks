#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from lib.config.minecraft import MINECRAFT_PROPS
from lib.stacks.game_stack import GameStack
from lib.stacks.minecraft_stack import MinecraftStack

app = App()
env = Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]
)

minecraft_stack = MinecraftStack(scope=app, props=MINECRAFT_PROPS, env=env)
app.synth()
