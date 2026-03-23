from unittest.mock import patch

import boto3
import pytest
from botocore.stub import Stubber


@pytest.fixture(scope="session")
def aws_region_name():
    return "us-east-1"


@pytest.fixture(scope="session")
def aws_account_id():
    return "00000000000"


@pytest.fixture(scope="session")
def aws_access_key_id():
    return "fake-access-key-id"


@pytest.fixture(scope="session")
def aws_secret_access_key():
    return "fake-secret-access-key"


@pytest.fixture(scope="session")
def aws_session_token():
    return "fake-session-token"


@pytest.fixture
def cluster_arn():
    return "arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster"


@pytest.fixture
def service_name():
    return "TestService"


@pytest.fixture(autouse=True)
def boto_session(aws_region_name, aws_access_key_id, aws_secret_access_key, aws_session_token):
    return boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=aws_region_name,
    )


@pytest.fixture
def boto_session_patch(boto_session):
    with (
        patch("boto3.Session", autospec=True) as m,
        patch("boto3.session.Session", autospec=True) as m2,
    ):
        m.return_value = boto_session
        m2.return_value = boto_session
        yield m


@pytest.fixture(autouse=True)
def boto_resource_patch(boto_session, boto_session_patch, ecs_client, ssm_client):
    def client(service, *args, **kwargs):
        if service == "ecs":
            return ecs_client
        if service == "ssm":
            return ssm_client
        raise ValueError(f"client for {service} not recognized")

    with patch.object(boto_session, "client", client):
        yield


@pytest.fixture(autouse=True)
def setup_environment(
    monkeypatch,
    aws_region_name,
    aws_access_key_id,
    aws_secret_access_key,
    aws_session_token,
    cluster_arn,
    service_name,
):
    """Mock environment variables"""
    monkeypatch.setenv("AWS_REGION", aws_region_name)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", aws_access_key_id)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", aws_secret_access_key)
    monkeypatch.setenv("AWS_SESSION_TOKEN", aws_session_token)
    monkeypatch.setenv("ECS_CLUSTER_ARN", cluster_arn)
    monkeypatch.setenv("ECS_SERVICE_NAME", service_name)
    monkeypatch.setenv("WEBHOOK_TOKEN_SSM_PATH", "/test/webhook-token")


@pytest.fixture
def ecs_client(boto_session):
    return boto_session.client("ecs")


@pytest.fixture
def ecs_stubber(ecs_client):
    with Stubber(ecs_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


@pytest.fixture
def ssm_client(boto_session):
    return boto_session.client("ssm")


@pytest.fixture
def ssm_stubber(ssm_client):
    with Stubber(ssm_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()
