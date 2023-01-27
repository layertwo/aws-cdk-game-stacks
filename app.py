#!/usr/bin/env python3
import os

from aws_cdk import App, Environment

from lib.config import ALL_GAME_PROPS
from lib.stacks.game_stack import GameStack

app = App()
env = Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]
)

for props in ALL_GAME_PROPS:
    if props.enabled:
        GameStack(
            scope=app,
            props=props,
            env=env,
        )

app.synth()
