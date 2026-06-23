from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template

from cdk.stacks.github_oidc_stack import GithubOidcStack


def test_github_oidc_stack_synth():
    app = App(context={"@aws-cdk/core:enablePartitionLiterals": True})
    account = "000000000000"

    env = Environment(account=account, region="us-west-1")
    stack = GithubOidcStack(
        scope=app,
        stack_id="TestGithubStack",
        env=env,
        github_org="layertwo",
        github_repo="aws-cdk-game-stacks",
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "RoleName": "GitHubActionsDeployRole",
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Condition": {
                            "StringLike": {
                                "token.actions.githubusercontent.com:sub": "repo:layertwo/aws-cdk-game-stacks:*"
                            }
                        },
                        "Effect": "Allow",
                        "Principal": {
                            "Federated": {"Ref": Match.string_like_regexp(r"GitHubOidcProvider.*")}
                        },
                    }
                ],
                "Version": "2012-10-17",
            },
        },
    )
