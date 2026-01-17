# Agent Context Documentation

This document provides context for AI agents working on this project.

## Product Overview

AWS CDK infrastructure for deploying game servers on AWS using containerized workloads.

The project provides reusable CDK stacks that deploy game servers (currently Minecraft) on ECS with EC2 instances, including:
- Auto-scaling groups with spot instances for cost optimization
- EFS storage for persistent game data with automated backups
- Optional scheduled start/stop for cost savings
- DNS automation via Route53 and Lambda
- GitHub OIDC integration for CI/CD deployments

The architecture uses a base `GameStack` class that can be extended for specific games (e.g., `MinecraftStack`), making it easy to deploy different game servers with consistent infrastructure patterns.

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **IaC Framework**: AWS CDK (Cloud Development Kit) v2.186+
- **Package Manager**: Poetry
- **Cloud Provider**: AWS

### Key AWS Services
- ECS (Elastic Container Service) with EC2 launch type
- EFS (Elastic File System) for persistent storage
- Auto Scaling Groups with spot instances
- Lambda for DNS automation
- Route53 for DNS management
- EventBridge for event-driven automation
- CloudWatch for logging and monitoring

### Development Tools
- **Formatter**: Black (line length: 100)
- **Import Sorter**: isort (Black profile)
- **Linter**: flake8
- **Testing**: pytest with coverage (80% minimum)

### Common Commands

#### Setup
```bash
poetry install
```

#### CDK Operations
```bash
# Synthesize CloudFormation templates
cdk synth

# Deploy stacks
cdk deploy --all

# Destroy stacks
cdk destroy --all

# View differences
cdk diff
```

#### Code Quality
```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Lint code
poetry run flake8

# Run tests with coverage
poetry run pytest
```

#### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=lib --cov-report=html
```

### Build Output
- CDK synthesized templates: `build/cdk.out/`
- Test coverage reports: `htmlcov/`

## Project Structure

### Directory Layout

```
.
├── app.py                    # CDK app entry point - instantiates stacks
├── lib/                      # Main library code
│   ├── stacks/              # CDK stack definitions
│   │   ├── game_stack.py    # Base game server stack (reusable)
│   │   ├── minecraft_stack.py  # Minecraft-specific stack
│   │   └── github_oidc_stack.py  # GitHub OIDC for CI/CD
│   ├── constructs/          # Reusable CDK constructs
│   │   └── traefik.py       # Traefik reverse proxy construct
│   ├── config/              # Configuration and properties
│   │   ├── __init__.py      # GameProperties dataclass
│   │   └── minecraft.py     # Minecraft-specific config
│   └── aws_common/          # Shared AWS utilities
│       ├── ec2.py           # EC2 helper functions
│       ├── ecs.py           # ECS helper functions
│       └── iam.py           # IAM policy helpers
├── lambda/                   # Lambda function code
│   ├── asg_set_desired_capacity.py
│   ├── ecs_desired_task_count.py
│   └── ecs_update_r53.py    # DNS update automation
├── test/                     # Test suite
│   ├── conftest.py          # Pytest fixtures
│   └── stacks/              # Stack tests
└── build/                    # Build artifacts (gitignored)
```

### Architecture Patterns

#### Stack Inheritance
- `GameStack`: Base class for all game servers with common infrastructure (VPC, ECS, EFS, ASG)
- Game-specific stacks (e.g., `MinecraftStack`) extend `GameStack` and override methods as needed

#### Configuration Pattern
- Use frozen dataclasses (`GameProperties`, `GamePort`) for type-safe configuration
- Game configs live in `lib/config/` and are imported into `app.py`
- Environment variables passed to containers via `environment` dict

#### Naming Convention
- Stack resources use `qualify_name()` method: `{GameName}{ResourceType}` (e.g., "MinecraftVpc")
- Use PascalCase for CDK construct IDs
- Use snake_case for Python variables and methods

#### Resource Organization
- Use `@cached_property` for expensive resource creation to ensure single instantiation
- Common AWS utilities extracted to `lib/aws_common/` for reuse
- Constructs in `lib/constructs/` for complex, reusable components (e.g., Traefik)

#### Testing
- Tests mirror the `lib/` structure in `test/`
- Use CDK assertions (`Template.from_stack()`) for infrastructure testing
- Fixtures defined in `conftest.py` for reusable test data
