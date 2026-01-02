from typing import Optional

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct


class GithubOidcStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        github_org: str,
        github_repo: str,
        github_environment: Optional[str] = None,
        github_branch: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Instantiate github oidc stack"""
        super().__init__(scope, stack_id, **kwargs)

        # Create or reference the GitHub OIDC provider
        provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOidcProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # Build the subject claim for the trust policy
        subject_claim = f"repo:{github_org}/{github_repo}:"

        if github_environment:
            subject_claim += f"environment:{github_environment}"
        elif github_branch:
            subject_claim += f"ref:refs/heads/${github_branch}"
        else:
            # Allow any branch/environment
            subject_claim += "*"

        # Create IAM role that GitHub Actions can assume
        self.role = iam.Role(
            self,
            "GitHubActionsRole",
            role_name="GitHubActionsDeployRole",
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": subject_claim,
                    },
                },
            ),
            max_session_duration=Duration.hours(1),
        )

        self.role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "iam:ResourceTag/aws-cdk:bootstrap-role": [
                            "deploy",
                            "file-publishing",
                            "image-publishing",
                            "lookup",
                        ],
                    },
                },
            ),
        )

        # Output the role ARN for use in GitHub secrets
        CfnOutput(
            self,
            "GitHubActionsRoleArn",
            value=self.role.role_arn,
            description="ARN of the IAM role for GitHub Actions (add to GitHub secrets as AWS_ROLE_ARN)",
            export_name="GitHubActionsRoleArn",
        )

        # Output the OIDC provider ARN
        CfnOutput(
            self,
            "GitHubOidcProviderArn",
            value=provider.open_id_connect_provider_arn,
            description="ARN of the GitHub OIDC provider",
        )
