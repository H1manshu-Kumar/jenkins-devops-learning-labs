# Lab 3.4 — Jenkins Multibranch Pipeline
## Branch-Based CI/CD Automation with Git Flow

### Overview

This lab demonstrates how Jenkins Multibranch Pipelines automatically discover Git branches and create dedicated pipelines for each branch without manual job creation.

In modern DevOps environments, development teams create feature branches, bugfix branches, and release branches continuously. A Multibranch Pipeline enables Jenkins to:

- Detect new branches automatically
- Create pipelines dynamically
- Execute branch-specific workflows
- Support Git Flow and trunk-based development
- Reduce Jenkins administration overhead

---

# Learning Objectives

By completing this lab, you will be able to:

- Understand Multibranch Pipeline architecture
- Configure branch discovery in Jenkins
- Use `env.BRANCH_NAME`
- Implement branch-specific pipeline logic
- Automate Git Flow workflows
- Troubleshoot branch scanning issues
- Apply production deployment controls

---

# Real-World Scenario

A development team works using Git Flow.

```text
main
│
├── feature/login
├── feature/payment
├── feature/cart
├── bugfix/header
└── release/v1.0
```

Whenever a developer pushes code:

1. Jenkins discovers the branch
2. Creates a dedicated pipeline
3. Executes CI stages
4. Publishes build results
5. Applies branch-specific rules

No manual Jenkins job creation is required.

---

# Architecture

```text
Developer Push
      │
      ▼
 GitHub Repository
      │
      ▼
 Jenkins Multibranch Pipeline
      │
 ┌────┼────────────────────┐
 │    │                    │
 ▼    ▼                    ▼
main feature-login   feature-payment
 │         │                │
 ▼         ▼                ▼
CI/CD    CI/CD           CI/CD
```

---

# Prerequisites

Complete:

- Lab 3.1 – Static Agent
- Lab 3.2 – Docker Agent
- Lab 3.3 – Multi-Agent Pipeline

Required:

- Jenkins
- Git Plugin
- Pipeline Plugin
- GitHub Repository
- Jenkins Git Credentials

---

# Repository Structure

```text
phase-3-agents/
│
├── lab-3.1-static-agent/
├── lab-3.2-docker-agent/
├── lab-3.3-multi-agent/
│
└── lab-3.4-multibranch/
    ├── Jenkinsfile
    └── README.md
```

---

# Step 1 – Create Lab Directory

```bash
mkdir lab-3.4-multibranch
cd lab-3.4-multibranch

touch Jenkinsfile
touch README.md
```

Commit:

```bash
git add .
git commit -m "Add lab 3.4 structure"
git push origin main
```

---

# Step 2 – Create Jenkinsfile

```groovy
pipeline {

    agent any

    stages {

        stage('Branch Information') {
            steps {
                echo "Current Branch: ${env.BRANCH_NAME}"
            }
        }

        stage('Build') {
            steps {
                echo 'Building application'
            }
        }

        stage('Test') {
            steps {
                echo 'Executing tests'
            }
        }
    }

    post {
        always {
            echo "Pipeline completed for ${env.BRANCH_NAME}"
        }
    }
}
```

Commit and push.

---

# Step 3 – Create Multibranch Pipeline Job

Jenkins Dashboard

```text
New Item
```

Select:

```text
Multibranch Pipeline
```

Job Name:

```text
lab-3.4-multibranch
```

---

# Step 4 – Configure Branch Source

Add Source:

```text
Git
```

Repository:

```text
https://github.com/<username>/phase-3-agents.git
```

Configure credentials.

Save configuration.

---

# Step 5 – Scan Repository

Run:

```text
Scan Multibranch Pipeline Now
```

Expected:

```text
main discovered
```

Jenkins automatically creates:

```text
lab-3.4-multibranch
└── main
```

---

# Step 6 – Verify Main Branch

Build the main branch.

Expected output:

```text
Current Branch: main
Building application
Executing tests
```

---

# Step 7 – Create Feature Branch

```bash
git checkout -b feature-login
```

Update Jenkinsfile:

```groovy
stage('Feature Stage') {
    steps {
        echo 'Feature Login Build'
    }
}
```

Commit:

```bash
git add .
git commit -m "Add feature login stage"
git push origin feature-login
```

---

# Step 8 – Branch Discovery

Run:

```text
Scan Multibranch Pipeline Now
```

Expected:

```text
main discovered
feature-login discovered
```

Jenkins automatically creates:

```text
main
feature-login
```

No additional Jenkins configuration is required.

---

# Understanding BRANCH_NAME

Jenkins automatically exposes:

```groovy
env.BRANCH_NAME
```

Example:

```groovy
echo "${env.BRANCH_NAME}"
```

Possible output:

```text
main
feature-login
feature-payment
bugfix-header
```

---

# Production Branch Controls

Restrict deployments to production only from main.

```groovy
stage('Deploy Production') {

    when {
        branch 'main'
    }

    steps {
        echo 'Deploying to Production'
    }
}
```

Benefits:

- Prevents accidental production deployment
- Enforces release governance
- Supports Git Flow standards

---

# Enterprise Deployment Strategy

| Branch | Environment |
|----------|-------------|
| main | Production |
| develop | QA |
| release/* | Staging |
| feature/* | Temporary Test Environment |

---

# Break-It Exercise 1 – Missing Jenkinsfile

### Action

Delete Jenkinsfile.

```bash
rm Jenkinsfile
git add .
git commit -m "Remove Jenkinsfile"
git push
```

### Expected Failure

```text
No Jenkinsfile found
```

### Root Cause

Multibranch Pipeline requires a Jenkinsfile in the branch root.

### Fix

Restore Jenkinsfile and push again.

---

# Break-It Exercise 2 – Incorrect Branch Condition

Change:

```groovy
branch 'main'
```

To:

```groovy
branch 'master'
```

### Expected Result

Deployment stage skipped.

### Root Cause

Branch name mismatch.

### Fix

Restore correct branch name.

---

# Break-It Exercise 3 – Invalid Repository URL

Configure an incorrect Git repository URL.

### Expected Failure

```text
Failed to fetch repository
```

### Root Cause

Jenkins cannot access repository metadata.

### Fix

Restore correct repository URL and rescan.

---

# Common Interview Questions

## What is a Multibranch Pipeline?

A Jenkins job type that automatically discovers repository branches and creates independent pipelines for each branch.

---

## Why use Multibranch Pipelines?

- Automatic branch discovery
- Reduced administration effort
- Git Flow support
- Better scalability

---

## What is BRANCH_NAME?

An environment variable automatically populated by Jenkins containing the current branch name.

---

## How do you deploy only from main?

```groovy
when {
    branch 'main'
}
```

---

## Pipeline vs Multibranch Pipeline

| Pipeline | Multibranch Pipeline |
|-----------|---------------------|
| Single branch | Multiple branches |
| Manual setup | Auto-discovery |
| Limited scalability | Highly scalable |
| Basic CI/CD | Git Flow friendly |

---

# Key Takeaways

- Jenkins can automatically discover Git branches.
- Every branch can have independent pipeline execution.
- BRANCH_NAME enables dynamic behavior.
- Production deployments should be restricted by branch.
- Multibranch Pipelines significantly reduce operational overhead.
- Branch discovery is foundational for enterprise CI/CD platforms.

---

# Portfolio Highlights

This lab demonstrates:

- Jenkins Multibranch Pipelines
- Git Flow Automation
- Branch-Based CI/CD
- Production Deployment Controls
- Enterprise Jenkins Practices
- Troubleshooting and Root Cause Analysis

These skills are frequently evaluated in DevOps interviews and are widely used in production Jenkins environments.
