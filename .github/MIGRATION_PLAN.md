# CI/CD Migration Plan

This document outlines the step-by-step migration from the current complex workflow architecture to a clean, maintainable CI/CD system.

## Current State Analysis

### Existing Workflows (TO BE REPLACED)
- `ci-cd.yml` - 571 lines, webhook-handler specific, overly complex
- `deploy-develop.yml` - 312 lines, environment deployment with complex logic  
- `deploy-production.yml` - 283 lines, production deployment
- `webhook-handler-ci.yml` - 333 lines, redundant webhook testing

**Total: 1,499 lines of duplicative workflow code**

### New Architecture (CLEAN & EFFICIENT)
- `webhook-handler.yml` - Clean service-specific CI/CD
- `activity-generator.yml` - Dedicated activity generator pipeline
- `mcp-server.yml` - MCP server deployment pipeline
- `deploy-environment.yml` - Reusable environment deployment
- Shared composite actions in `.github/actions/`

**Estimated: 800 lines total (47% reduction)**

## Migration Steps

### Phase 1: Setup New Infrastructure ✅ COMPLETED
- [x] Created reusable composite actions
- [x] Created clean service-specific workflows
- [x] Created environment deployment workflow

### Phase 2: Validation & Testing (NEXT STEPS)

1. **Test New Workflows**
   ```bash
   # Test on a feature branch first
   git checkout -b test-new-cicd
   git push origin test-new-cicd
   
   # Trigger webhook-handler workflow
   touch webhook-handler/test-trigger.txt
   git add . && git commit -m "Test new webhook CI/CD"
   git push
   ```

2. **Validate Service Separation**
   - Test that webhook-handler changes only trigger webhook workflow
   - Test that activity-generator changes only trigger activity workflow
   - Test that MCP changes only trigger MCP workflow

3. **Verify Environment Deployments**
   - Test development environment deployment
   - Test production environment deployment (with manual approval)

### Phase 3: Migration Execution

1. **Rename Old Workflows (Safe Backup)**
   ```bash
   cd .github/workflows/
   mv ci-cd.yml ci-cd.yml.backup
   mv deploy-develop.yml deploy-develop.yml.backup  
   mv deploy-production.yml deploy-production.yml.backup
   mv webhook-handler-ci.yml webhook-handler-ci.yml.backup
   ```

2. **Activate New Workflows**
   - New workflows are already in place and ready
   - They will automatically trigger on next push to main/develop

3. **Clean Repository Secrets**
   ```bash
   # Update GitHub repository settings:
   # - Ensure AWS_ROLE_TO_ASSUME_DEV is set
   # - Ensure AWS_ROLE_TO_ASSUME_PROD is set
   # - Remove any old hardcoded credentials
   ```

### Phase 4: Optimization

1. **Remove Backup Files** (after 2 weeks of stable operation)
   ```bash
   rm .github/workflows/*.backup
   ```

2. **Clean Up Deployment Artifacts**
   ```bash
   # Remove old deployment directories and files
   rm -rf lambda-deployment/
   rm -rf lambda_package/
   rm *.zip  # Remove old deployment zips
   ```

## Benefits of New Architecture

### 🚀 Performance Improvements
- **47% reduction in workflow code**
- **Parallel service builds** instead of sequential
- **Smart path-based triggering** - only affected services rebuild
- **Cached dependencies** across all workflows

### 🔒 Security Enhancements
- **OIDC authentication** everywhere
- **No hardcoded credentials** in workflows
- **Least privilege** service separation
- **Environment-specific permissions**

### 🛠️ Maintainability
- **DRY principle** - reusable composite actions
- **Clear service boundaries** - one workflow per service  
- **Consistent patterns** across all services
- **Easy to add new services** using established patterns

### 📊 Developer Experience
- **Faster feedback** - targeted builds
- **Clear failure points** - know exactly which service failed
- **Better logs** - focused on relevant service
- **Easier debugging** - simpler workflow logic

## Testing Checklist

### Pre-Migration Tests
- [ ] Webhook handler builds successfully
- [ ] Activity generator builds successfully  
- [ ] MCP server builds successfully
- [ ] Development deployment works
- [ ] Production deployment works (with approval)
- [ ] Rollback functionality works
- [ ] Security scans pass
- [ ] Coverage reports generate

### Post-Migration Validation
- [ ] All services deploy independently
- [ ] No interference between service deployments
- [ ] Environment promotions work correctly
- [ ] Terraform deployments work
- [ ] AWS permissions are correct
- [ ] Artifact cleanup works
- [ ] GitHub environment protections work

## Rollback Plan

If issues occur, immediately restore old workflows:

```bash
cd .github/workflows/
mv ci-cd.yml.backup ci-cd.yml
mv deploy-develop.yml.backup deploy-develop.yml
mv deploy-production.yml.backup deploy-production.yml
mv webhook-handler-ci.yml.backup webhook-handler-ci.yml

# Disable new workflows temporarily
mv webhook-handler.yml webhook-handler.yml.disabled
mv activity-generator.yml activity-generator.yml.disabled
mv mcp-server.yml mcp-server.yml.disabled
```

## Support & Troubleshooting

### Common Issues

1. **Path Detection Problems**
   - Ensure service paths match exactly in workflow triggers
   - Use `git diff --name-only` to verify paths

2. **AWS Permission Issues**
   - Verify OIDC role has correct Lambda permissions
   - Check that role trust policy includes GitHub OIDC

3. **Build Failures**
   - Check that requirements.txt files exist
   - Verify Python version compatibility
   - Ensure source code structure matches expected layout

4. **Deployment Issues**
   - Verify Lambda function names match exactly
   - Check AWS region is correct
   - Ensure functions exist before attempting updates

## Next Steps

1. **Review and approve** this migration plan
2. **Test on feature branch** before main migration
3. **Schedule migration** during low-traffic period
4. **Monitor closely** for first 48 hours post-migration
5. **Clean up old files** after 2 weeks of stable operation

---

**Migration Owner:** CI/CD Architect  
**Target Completion:** Next deployment window  
**Rollback Time:** < 5 minutes