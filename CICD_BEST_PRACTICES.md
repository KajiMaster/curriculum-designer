# CI/CD Best Practices - Universal Portfolio Rules

> **Created**: 2025-09-05  
> **Purpose**: Universal CI/CD guidelines extracted from real-world debugging session  
> **Status**: Production-ready, ready to pivot to parent project

## 🎯 **Core Principle: CI/CD First, CLI Never**

**Golden Rule**: If it can be deployed via CI/CD, it MUST be deployed via CI/CD. CLI deployments are for emergencies only and indicate a broken pipeline.

---

## 🏗️ **Infrastructure Deployment Strategy**

### **Two-Tier Architecture**

#### **Tier 1: Global Infrastructure (Manual)**
- **What**: Shared resources, databases, layers, core functions
- **When**: Before pushing code changes  
- **How**: Manual Terraform CLI from `terraform/environments/global`
- **Why**: Prevent accidental destroys, requires careful consideration

```bash
# Proper global deployment sequence
cd ~/project-root/terraform/environments/global
terraform plan
terraform apply  # Only after careful review
```

#### **Tier 2: Environment Infrastructure (Automated)**
- **What**: Environment-specific Lambdas, API Gateway, per-env resources
- **When**: Automatically on git push
- **How**: GitHub Actions with smart change detection
- **Why**: Fast iteration, consistent deployments, proper testing

### **Integration Pattern**
1. **Deploy global manually** → 2. **Push code changes** → 3. **CI/CD handles environment deployment**

---

## 📋 **Deployment Workflow Rules**

### **Rule 1: Always Verify CI/CD Status**
```bash
# NEVER assume deployment worked - always verify
gh run list --limit 3
gh run view [run-id]

# Check actual function timestamps
aws lambda list-functions --query 'Functions[?contains(FunctionName,`project-name`)].[FunctionName,LastModified]'
```

### **Rule 2: CI/CD Failure = Stop Everything**
- If CI/CD fails, fix the pipeline BEFORE continuing
- CLI deployment is NOT a substitute for broken CI/CD
- Document the root cause and fix for future reference

### **Rule 3: Use Change Detection Logic**
```yaml
# Smart change detection pattern
if echo "$CHANGED_FILES" | grep -qE "^lambda/"; then
  echo "lambda=true" >> $GITHUB_OUTPUT
  echo "📦 Lambda changes detected - will build and deploy all Lambda functions"
else
  echo "lambda=false" >> $GITHUB_OUTPUT
fi
```

### **Rule 4: Force Deploy When Needed**
```yaml
# Manual workflow dispatch for edge cases
workflow_dispatch:
  inputs:
    force_deploy:
      description: 'Force deploy all components'
      required: false
      default: false
      type: boolean
```

---

## 🔧 **Change Detection Best Practices**

### **File Path Patterns**
```yaml
# Lambda changes
"^lambda/"
# Terraform changes  
"^terraform/.*\.tf$"
# Global terraform (if auto-enabled)
"^terraform/environments/global/.*\.tf$"
# Multi-env terraform
"^terraform/environments/multi-env/.*\.tf$"
```

### **Trigger Logic**
- **ANY Lambda change** → Build and deploy ALL Lambdas
- **Terraform change** → Apply relevant infrastructure
- **Workflow files change** → Skip deployments (unless force_deploy)

---

## 🎯 **Artifact Management**

### **Build Once, Deploy Everywhere**
```bash
# CI/CD builds artifacts
./lambda-deployments/build.sh  # Builds all functions
# Uploads artifacts to GitHub Actions
# Downloads artifacts in deployment jobs
# Uses same artifacts for all environments
```

### **Artifact Verification**
```bash
# Verify artifacts were built by CI/CD, not local
ls -la lambda-deployments/*/deployment.zip
# Check timestamps match CI/CD run time
```

---

## 🚨 **Common Pitfalls & Solutions**

### **Pitfall 1: "It Deployed But Nothing Changed"**
**Symptoms**: 
- CI/CD shows success
- Functions still have old code
- Jobs show "skipped" status

**Root Cause**: Change detection failed or wrong files changed

**Solution**:
```bash
# Verify what actually deployed
gh run view [run-id]
# Check if jobs were skipped (dashed lines)
# Make small change to trigger proper deployment
```

### **Pitfall 2: "Permissions Error in CI/CD"**
**Symptoms**: 
- Terraform apply fails with permissions
- IAM or resource access denied

**Root Cause**: CI/CD role lacks necessary permissions

**Solutions**:
1. Update IAM policy in Terraform
2. Move problematic resources to manual (global) tier
3. Use targeted applies to avoid problematic resources

### **Pitfall 3: "Manual CLI Deployment Temptation"**
**Symptoms**: 
- CI/CD is broken
- Deadline pressure
- "Just this once" mentality

**Rule**: Fix the CI/CD first. Period.

**Exception**: Global infrastructure only.

---

## 📊 **Quality Gates**

### **Pre-Push Checklist**
- [ ] Global infrastructure applied if needed
- [ ] Local tests pass
- [ ] Change detection will trigger correctly
- [ ] No sensitive data in commits

### **Post-Push Verification**
- [ ] CI/CD triggered correctly
- [ ] All expected jobs ran (not skipped)
- [ ] Function timestamps updated
- [ ] Manual verification of key functionality

### **Deployment Health Check**
```bash
# Automated health checks
aws lambda get-function --function-name [function-name]
# Test key endpoints
curl [api-endpoint]/health
```

---

## 📝 **Documentation Requirements**

### **Every Project Must Have**
1. **README.md** with deployment instructions
2. **Architecture diagrams** showing CI/CD flow
3. **Runbook** for common issues
4. **Change log** of CI/CD evolution

### **Incident Response**
1. Document what broke
2. Document the fix
3. Update CI/CD to prevent recurrence
4. Update this document with lessons learned

---

## 🔄 **Evolution Guidelines**

### **When to Update This Document**
- New deployment pattern discovered
- CI/CD pipeline significantly changed
- New tools or platforms adopted
- Major incident with lessons learned

### **Migration to Parent Project**
This document is designed to be:
- Framework agnostic (works with AWS, GCP, Azure)
- Language agnostic (Python, Node.js, etc.)
- Tool agnostic (GitHub Actions, GitLab CI, etc.)

When moving to parent project:
1. Generalize AWS-specific examples
2. Add multi-cloud patterns
3. Include container deployment patterns
4. Add compliance and security sections

---

## 🎪 **Real-World Example: This Project**

### **What We Learned**
1. **Change detection is critical** - workflow changes don't trigger Lambda deployments
2. **Permissions creep** - DynamoDB TTL permissions broke global deployments
3. **Manual deployment trap** - CLI deployments felt faster but broke the process
4. **Verification is key** - "deployed" doesn't mean "working"

### **What We Fixed**
1. Removed problematic global resources from CI/CD
2. Added manual workflow dispatch for edge cases
3. Created proper two-tier deployment strategy
4. Enhanced change detection logic

### **Current State**
- ✅ Global: Manual deployment via CLI (activity-generator, frameworks table)  
- ✅ Multi-env: Automated deployment via CI/CD (webhook-handler)
- ✅ Smart change detection based on file paths
- ✅ Artifact-based deployment consistency

---

## 🚀 **Quick Reference Commands**

```bash
# Check CI/CD status
gh run list --limit 3

# Force manual deployment (only if CI/CD broken)
gh workflow run .github/workflows/deploy-develop.yml --field force_deploy=true

# Global infrastructure deployment
cd terraform/environments/global && terraform apply

# Verify Lambda deployment
aws lambda list-functions --query 'Functions[?contains(FunctionName,`project`)].[FunctionName,LastModified]'

# Check function health
aws lambda invoke --function-name [name] test_output.json
```

---

## 📚 **Related Documentation**
- [LAMBDA_BEST_PRACTICES.md](./LAMBDA_BEST_PRACTICES.md) - Lambda-specific guidelines
- [PROJECT_ARCHITECTURE.md](./PROJECT_ARCHITECTURE.md) - System architecture overview
- [GitHub Actions Workflows](./github/workflows/) - Implementation details

---

**Remember**: CI/CD is not just about automation - it's about consistency, reliability, and preventing human error. Treat it as a first-class citizen in your development process.