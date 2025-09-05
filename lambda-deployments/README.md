# Lambda Deployments

This directory contains build artifacts for Lambda functions. **Do not commit the deployment artifacts** - they are built automatically by CI/CD.

## Directory Structure

```
lambda-deployments/
├── build.sh                    # Universal build script
├── README.md                   # This file
├── activity-generator/         # Built by CI/CD (gitignored)
│   └── deployment.zip
├── webhook-handler/            # Built by CI/CD (gitignored)
│   └── deployment.zip
└── mcp-server/                 # Built by CI/CD (gitignored)
    └── deployment.zip
```

## Usage

### Build All Functions
```bash
./build.sh
```

### Build Specific Function
```bash
./build.sh activity-generator
./build.sh webhook-handler
./build.sh mcp-server
```

## CI/CD Integration

GitHub Actions workflows automatically:
1. Run `./build.sh {function-name}` to create deployment packages
2. Deploy using Terraform or AWS CLI
3. Update function code and configuration

## Source Code Structure

Lambda source code is organized in `/lambda/` with this structure:
- `/lambda/{function-name}/lambda_function.py` - Standard handler
- `/lambda/{function-name}/requirements.txt` - Dependencies
- `/lambda/{function-name}/tests/` - Unit tests (optional)

See [LAMBDA_BEST_PRACTICES.md](../LAMBDA_BEST_PRACTICES.md) for detailed guidelines.