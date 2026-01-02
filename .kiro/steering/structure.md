# Project Structure

## Directory Layout

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

## Architecture Patterns

### Stack Inheritance
- `GameStack`: Base class for all game servers with common infrastructure (VPC, ECS, EFS, ASG)
- Game-specific stacks (e.g., `MinecraftStack`) extend `GameStack` and override methods as needed

### Configuration Pattern
- Use frozen dataclasses (`GameProperties`, `GamePort`) for type-safe configuration
- Game configs live in `lib/config/` and are imported into `app.py`
- Environment variables passed to containers via `environment` dict

### Naming Convention
- Stack resources use `qualify_name()` method: `{GameName}{ResourceType}` (e.g., "MinecraftVpc")
- Use PascalCase for CDK construct IDs
- Use snake_case for Python variables and methods

### Resource Organization
- Use `@cached_property` for expensive resource creation to ensure single instantiation
- Common AWS utilities extracted to `lib/aws_common/` for reuse
- Constructs in `lib/constructs/` for complex, reusable components (e.g., Traefik)

### Testing
- Tests mirror the `lib/` structure in `test/`
- Use CDK assertions (`Template.from_stack()`) for infrastructure testing
- Fixtures defined in `conftest.py` for reusable test data
