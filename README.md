# AWS CDK Game Stacks

Infrastructure as Code for deploying containerized game servers on AWS using the AWS Cloud Development Kit (CDK).

## Overview

This project provides reusable CDK stacks for deploying game servers (currently Minecraft) on AWS ECS with EC2 instances. It's designed with cost optimization and automation in mind, featuring:

- **Cost-Optimized Infrastructure**: Spot instances with auto-scaling groups
- **Persistent Storage**: EFS with automated backups and lifecycle policies
- **Automated DNS**: Lambda-based Route53 updates when servers start
- **Scheduled Operations**: Optional auto-start/stop for cost savings
- **On-Demand Webhook**: Lambda Function URL to start/stop servers via HTTP
- **Extensible Architecture**: Base `GameStack` class for easy multi-game support
- **CI/CD Ready**: GitHub OIDC integration for secure deployments

## Architecture

### Core Components

- **ECS Cluster**: Runs containerized game servers on EC2 instances
- **Auto Scaling Group**: Manages spot instances with capacity rebalancing
- **EFS Storage**: Persistent game data with automated backups
- **Lambda Functions**: DNS automation and operational tasks
- **EventBridge**: Event-driven automation for server lifecycle
- **Route53**: Automatic DNS updates when servers start

### Stack Inheritance Pattern

The project uses a base `GameStack` class that provides common infrastructure:
- VPC with public subnets
- ECS cluster with ASG capacity provider
- EFS file system with backup plan
- Security groups and IAM roles
- Optional scheduled start/stop
- Optional DNS automation

Game-specific stacks (e.g., `MinecraftStack`) extend `GameStack` and customize as needed.

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- AWS CLI configured with appropriate credentials
- AWS CDK CLI: `npm install -g aws-cdk`
- [uv](https://docs.astral.sh/uv/) (optional, for Lambda development)

## Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure AWS Environment

```bash
export CDK_DEFAULT_ACCOUNT="your-account-id"
export CDK_DEFAULT_REGION="ca-central-1"
```

### 3. Bootstrap CDK (first time only)

```bash
cdk bootstrap
```

### 4. Deploy

```bash
# Preview changes
cdk diff

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy MinecraftStack
```

## Configuration

### Game Properties

Game configurations are defined in `lib/config/` using the `GameProperties` dataclass:

```python
from lib.config import GameProperties, GamePort, PortType

MINECRAFT_PROPS = GameProperties(
    name="Minecraft",
    container_image="itzg/minecraft-server:java17-jdk",
    container_path="/data",
    ports=[GamePort(port_type=PortType.TCP, number=25565)],
    environment={
        "TYPE": "PAPER",
        "VERSION": "1.20.4",
        # ... additional environment variables
    },
    auto_start=False,
    start_time="0 23 * * FRI",  # Friday 3PM PST
    stop_time="0 6 * * MON",    # Sunday 10PM PST
    domain_name="g.example.com",
    hosted_zone_id="Z0123456789ABCDEFGHIJ",
    instance_type="t4g.large",
    max_mib_memory=6144,
)
```

### Adding a New Game

1. Create a config file in `lib/config/your_game.py`
2. Define game properties using `GameProperties`
3. Create a stack class in `lib/stacks/your_game_stack.py` extending `GameStack`
4. Add the stack to `app.py`

## Project Structure

```
.
├── app.py                    # CDK app entry point
├── lib/
│   ├── stacks/              # CDK stack definitions
│   │   ├── game_stack.py    # Base game server stack
│   │   ├── minecraft_stack.py
│   │   └── github_oidc_stack.py
│   ├── constructs/          # Reusable CDK constructs
│   ├── config/              # Game configurations
│   └── aws_common/          # Shared AWS utilities
├── lambda/                   # Lambda function code
│   ├── asg_set_desired_capacity.py
│   ├── ecs_desired_task_count.py
│   └── ecs_update_r53.py
└── test/                     # Test suite
```

## Development

### Code Quality

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Lint code
poetry run flake8
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=lib --cov-report=html
```

Minimum test coverage: 80%

### CDK Commands

```bash
# Synthesize CloudFormation templates
cdk synth

# View differences between deployed and local
cdk diff

# Deploy stacks
cdk deploy --all

# Destroy stacks
cdk destroy --all

# List all stacks
cdk list
```

## Cost Optimization

- **Spot Instances**: Up to 90% savings vs on-demand pricing
- **Scheduled Scaling**: Auto-stop during off-hours
- **EFS Lifecycle**: Automatic transition to Infrequent Access after 7 days
- **Elastic Throughput**: EFS scales automatically, pay only for what you use
- **ARM Architecture**: t4g instances offer better price-performance

## Security

- **IMDSv2**: Required on all EC2 instances
- **Security Groups**: Minimal ingress rules, game ports only
- **IAM Roles**: Least-privilege policies for Lambda and EC2
- **EFS Encryption**: Transit encryption enabled
- **GitHub OIDC**: No long-lived AWS credentials in CI/CD

## Monitoring

- **CloudWatch Logs**: Centralized logging for Lambda and ECS
- **ECS Task Events**: Automated DNS updates on task state changes
- **Auto Scaling Metrics**: Track capacity and spot interruptions

## On-Demand Webhook

The stack exposes a Lambda Function URL that lets you start or stop the server on demand without AWS console access.

### Setup

Store a secret token in SSM (first time only):

```bash
aws ssm put-parameter \
  --name /minecraft/webhook-token \
  --type SecureString \
  --value <your-secret-token>
```

### Usage

**Start the server:**

```bash
curl -X POST \
  -H "x-webhook-token: <your-secret-token>" \
  -H "Content-Type: application/json" \
  <lambda-function-url> \
  -d '{"action":"start"}'
```

**Stop the server:**

```bash
curl -X POST \
  -H "x-webhook-token: <your-secret-token>" \
  -H "Content-Type: application/json" \
  <lambda-function-url> \
  -d '{"action":"stop"}'
```

The Lambda Function URL is output by CDK after deployment. Successful responses return `{"status": "ok", "desired_count": 1}` (start) or `{"status": "ok", "desired_count": 0}` (stop).

## Troubleshooting

### Server Won't Start

Check ECS task logs:
```bash
aws ecs describe-tasks --cluster MinecraftCluster --tasks <task-id>
```

### DNS Not Updating

Check Lambda logs:
```bash
aws logs tail /minecraft/MinecraftDnsUpdateLambda --follow
```

### Spot Instance Interrupted

The ASG will automatically launch a replacement instance. Game data persists on EFS.

## Contributing

1. Follow the existing code structure and patterns
2. Maintain test coverage above 80%
3. Run code quality tools before committing
4. Use conventional commit messages

## License

Apache-2.0

## Author

Lucas Messenger ([@layertwo](https://github.com/layertwo))
