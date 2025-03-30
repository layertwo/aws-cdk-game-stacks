from aws_cdk import App, Environment
from aws_cdk.assertions import Template

from lib.config import GameProperties
from lib.stacks.game_stack import GameStack


def test_game_stack_synth(game_properties: GameProperties):
    app = App()
    env = Environment(account="000000000000", region="us-west-1")
    stack = GameStack(scope=app, props=game_properties, env=env)

    Template.from_stack(stack)
    assert True
