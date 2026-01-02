# Technology Stack

## Core Technologies
- **Language**: Python 3.11+
- **IaC Framework**: AWS CDK (Cloud Development Kit) v2.186+
- **Package Manager**: Poetry
- **Cloud Provider**: AWS

## Key AWS Services
- ECS (Elastic Container Service) with EC2 launch type
- EFS (Elastic File System) for persistent storage
- Auto Scaling Groups with spot instances
- Lambda for DNS automation
- Route53 for DNS management
- EventBridge for event-driven automation
- CloudWatch for logging and monitoring

## Development Tools
- **Formatter**: Black (line length: 100)
- **Import Sorter**: isort (Black profile)
- **Linter**: flake8
- **Testing**: pytest with coverage (80% minimum)

## Common Commands

### Setup
```bash
poetry install
```

### CDK Operations
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

### Code Quality
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

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=lib --cov-report=html
```

## Build Output
- CDK synthesized templates: `build/cdk.out/`
- Test coverage reports: `htmlcov/`
