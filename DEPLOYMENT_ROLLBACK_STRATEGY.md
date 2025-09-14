# Deployment and Rollback Strategy

## ESL Fix Deployment Overview

This document outlines the deployment strategy and rollback procedures for the ESL level fixes to the curriculum designer system.

## Changes Implemented

### 1. Lambda Functions Updated
- **webhook-handler**: Updated command parsing to use `esl_level` instead of `grade_level`
- **activity-generator**: Updated to handle ESL terminology and adult learner contexts

### 2. Infrastructure Optimizations
- **Memory**: Increased activity-generator memory from 512MB to 1024MB for better AI performance
- **Timeout**: Extended activity-generator timeout from 60s to 90s for complex activities
- **Monitoring**: Added X-Ray tracing, CloudWatch alarms, and SQS dead letter queue
- **Cost Control**: Added reserved concurrency limit of 5 for activity-generator

### 3. Database Schema Updates
- **DynamoDB**: Changed `grade_level` to `esl_level` in activities table
- **TTL**: Added automatic cleanup after 1 year to control storage costs
- **Recovery**: Enabled point-in-time recovery for data protection

### 4. CI/CD Pipeline Updates
- **GitHub Actions**: Updated test payloads to use ESL terminology
- **Terraform**: Updated infrastructure definitions for ESL schema

## Deployment Process

### Phase 1: Infrastructure Updates
```bash
# Deploy Terraform changes for optimized Lambda configuration
cd terraform/environments/global
terraform plan
terraform apply

# Verify DynamoDB schema migration
aws dynamodb describe-table --table-name curriculum-activities
```

### Phase 2: Lambda Deployment
```bash
# Deploy activity generator
cd lambda-deployments
./build-activity-generator.sh
aws lambda update-function-code \
  --function-name curriculum-activity-generator \
  --zip-file fileb://activity-generator/deployment.zip

# Deploy webhook handler  
./build-webhook-handler.sh
aws lambda update-function-code \
  --function-name curriculum-designer-webhook-prod \
  --zip-file fileb://webhook-handler/deployment.zip
```

### Phase 3: Validation
```bash
# Test activity generation with new ESL format
aws lambda invoke \
  --function-name curriculum-activity-generator \
  --payload '{"body": "{\"topic\": \"coffee farming\", \"esl_level\": \"intermediate\", \"duration\": 15}"}' \
  test_response.json

# Verify webhook handler parsing
# Trello command: @ai generate activity "coffee farming" intermediate
```

## Rollback Strategy

### Emergency Rollback (< 5 minutes)
If critical issues are detected immediately after deployment:

1. **Lambda Function Rollback**:
```bash
# Revert to previous version using Lambda aliases
aws lambda update-alias \
  --function-name curriculum-activity-generator \
  --name PROD \
  --function-version $PREVIOUS_VERSION

aws lambda update-alias \
  --function-name curriculum-designer-webhook-prod \
  --name PROD \
  --function-version $PREVIOUS_VERSION
```

2. **Traffic Routing**: Update API Gateway to route to previous versions if needed

### Database Schema Rollback
If DynamoDB schema issues occur:

1. **Backup Current Data**:
```bash
# Create backup before rollback
aws dynamodb create-backup \
  --table-name curriculum-activities \
  --backup-name esl-fix-rollback-$(date +%Y%m%d-%H%M%S)
```

2. **Schema Migration Script** (if needed):
```python
# Convert esl_level back to grade_level temporarily
# This would be a custom script to migrate data
```

### Monitoring During Rollback
- Monitor CloudWatch alarms for error rates
- Check X-Ray traces for performance issues
- Verify DynamoDB read/write capacity
- Monitor Lambda concurrency and duration

## Post-Deployment Verification

### 1. Functional Tests
- [ ] Trello webhook responds to @ai commands
- [ ] Activity generation works with ESL levels
- [ ] Error handling works properly
- [ ] Database writes succeed

### 2. Performance Tests
- [ ] Lambda cold start times < 5s
- [ ] Activity generation completes < 60s
- [ ] Memory usage within limits
- [ ] No throttling errors

### 3. Cost Monitoring
- [ ] Lambda invocation costs within budget
- [ ] DynamoDB costs optimized with TTL
- [ ] No unexpected charges from increased memory

## Rollback Triggers

Immediately rollback if:
- Error rate > 10% for 5 minutes
- Average duration > 75 seconds
- Any security alerts
- Data corruption detected
- User reports of complete service failure

## Communication Plan

### Internal Notifications
- DevOps team: Immediate Slack notification
- Product team: Status update within 30 minutes
- Management: Summary within 1 hour if rollback required

### External Communications
- Teachers/Users: Only if service disruption > 15 minutes
- Status page update if rollback affects multiple users

## Success Criteria

Deployment is considered successful when:
- All automated tests pass
- Manual testing confirms ESL terminology works
- Performance metrics are within acceptable ranges
- No error alarms triggered for 24 hours
- User feedback is positive

## Lessons Learned Process

After deployment completion:
1. Document any issues encountered
2. Update rollback procedures based on experience
3. Review monitoring thresholds
4. Update deployment automation
5. Share knowledge with team

## Emergency Contacts

- DevOps Lead: [Insert contact]
- AWS Administrator: [Insert contact]
- Product Owner: [Insert contact]
- On-call Engineer: [Insert contact]

---
*Document Version: 1.0*  
*Last Updated: 2025-01-14*  
*Next Review: After deployment completion*