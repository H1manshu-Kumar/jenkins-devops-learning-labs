# 🚀 Lab 3.2 - Jenkins Docker Agents (Ephemeral CI/CD Builds)

<div align="center">

![Jenkins](https://img.shields.io/badge/Jenkins-Docker%20Agents-red?style=for-the-badge&logo=jenkins)
![Docker](https://img.shields.io/badge/Docker-Ephemeral%20Builds-blue?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/Python-3.11--slim-yellow?style=for-the-badge&logo=python)
![Pytest](https://img.shields.io/badge/Tested%20With-pytest-green?style=for-the-badge&logo=pytest)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)

</div>

---

# 📌 Overview

In this lab, I replaced a **static Jenkins SSH agent** with an **ephemeral Docker agent**.

Instead of reusing a long-running machine/container, Jenkins now:

- Spins up a fresh Docker container for every build
- Runs the pipeline inside the container
- Publishes JUnit test reports
- Automatically destroys the container after execution

This simulates how modern CI/CD platforms work in production environments.

---

# 🎯 Learning Objectives

By completing this lab, I learned how to:

✅ Use Docker-based Jenkins agents  
✅ Build ephemeral CI/CD execution environments  
✅ Run pytest inside containers  
✅ Publish JUnit test reports in Jenkins  
✅ Debug Docker socket permission issues  
✅ Understand container lifecycle in Jenkins pipelines  
✅ Compare static vs dynamic Jenkins agents  
✅ Troubleshoot image pull failures and runtime issues  

---

# 🧠 Core Concept — Ephemeral Infrastructure

## 🔹 Static Agent vs Docker Agent

| Static SSH Agent | Docker Agent |
|---|---|
| Runs continuously | Created per build |
| Shared environment | Isolated environment |
| Manual maintenance | Disposable |
| Dependency conflicts possible | Fresh dependencies every run |
| Disk usage grows over time | Clean environment |
| SSH based | Docker based |

---

# 🏗️ Architecture Overview

```text
┌─────────────────────────────────────┐
│         Jenkins Controller          │
│                                     │
│  Reads Jenkinsfile                  │
│  Pulls Docker Image                 │
│  Spins up container                 │
│  Executes pipeline                  │
│  Archives test results              │
│  Destroys container                 │
└────────────────┬────────────────────┘
                 │
                 │ Docker API
                 ▼
┌─────────────────────────────────────┐
│       python:3.11-slim Container    │
│                                     │
│  - Installs pytest                  │
│  - Runs tests                       │
│  - Generates JUnit XML              │
│  - Removed after build              │
└─────────────────────────────────────┘
```

---

# 🧪 QA → DevOps Mapping

| QA Mindset | DevOps Equivalent |
|---|---|
| Fresh browser session | Fresh container per build |
| No leftover cache/cookies | No leftover filesystem state |
| Selenium Grid containers | Docker Jenkins agents |
| Test isolation | Build isolation |
| teardown() cleanup | Container auto-destruction |

---

# ⚙️ Tech Stack Used

| Tool | Purpose |
|---|---|
| Jenkins | CI/CD Orchestration |
| Docker | Ephemeral build environment |
| Python 3.11 | Runtime environment |
| pytest | Test execution |
| JUnit XML | Test reporting |
| Linux | Host OS |

---

# 📂 Project Structure

```text
phase-3-agents/
└── lab-3.2-docker-agent/
    ├── README.md
    ├── Jenkinsfile
    ├── setup-notes.md
    ├── results/
    │   └── .gitkeep
    ├── tests/
    │   └── test_sample.py
    └── screenshots/
        ├── successful-build.png
        ├── junit-results.png
        ├── break-exercise-1.png
        ├── break-exercise-2.png
        └── docker-container-proof.png
```

---

# 🐳 Final Jenkinsfile Used

```groovy
pipeline {

    agent {
        docker {
            image 'python:3.11-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -e HOME=/tmp'
        }
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {

        stage('Verify - Docker Agent Environment') {
            steps {
                sh 'echo "Hostname: $(hostname)"'
                sh 'echo "Whoami: $(whoami)"'
                sh 'echo "Python version: $(python3 --version)"'
                sh 'echo "Working dir: $(pwd)"'
                sh 'echo "Build number: ${BUILD_NUMBER}"'
                sh 'echo "Node Name: ${NODE_NAME}"'
            }
        }

        stage('Debug - List Files') {
            steps {
                sh 'ls -la phase-3-agents/lab-3.2-docker-agent/'
                sh 'ls -la phase-3-agents/lab-3.2-docker-agent/tests/'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install --user pytest --quiet'
                sh 'pip show pytest | grep Version'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    export PATH=/tmp/.local/bin:$PATH

                    cd phase-3-agents/lab-3.2-docker-agent

                    pytest tests/test_sample.py \
                        --junit-xml=results/test-results.xml \
                        --verbose \
                        -p no:cacheprovider
                '''
            }
        }

        stage('Verify - Container Will Be Destroyed') {
            steps {
                sh 'echo "Container ID: $(hostname)"'
                sh 'echo "This container will not exist after this build completes"'
            }
        }
    }

    post {

        always {
            junit 'phase-3-agents/lab-3.2-docker-agent/results/test-results.xml'

            echo "Build ${BUILD_NUMBER} complete — container will now be destroyed"
        }

        success {
            echo "SUCCESS — All tests passed inside Docker agent"
        }

        failure {
            echo "FAILURE — Check console log for errors inside container"
        }
    }
}
```

---

# 🔥 Key Features Implemented

✅ Dynamic Docker agent execution  
✅ Ephemeral build environment  
✅ Docker socket mounting  
✅ HOME workaround for pip permissions  
✅ Dynamic pytest installation  
✅ JUnit report publishing  
✅ Build timeout protection  
✅ Build retention policy  
✅ Container lifecycle verification  
✅ Debugging stages for troubleshooting  

---

# 💥 Break-It Exercises Completed

---

## ❌ Exercise 1 — Wrong Docker Image

### What I Changed

```groovy
image 'python:nonexistent-tag'
```

### What Happened

- Build failed immediately
- Docker image pull error appeared
- Pipeline stages never executed

### Key Learning

Docker agents fail fast when image pull fails.

Unlike static Jenkins agents:
- Wrong label → build waits forever
- Wrong image → immediate failure

---

## ❌ Exercise 2 — Removed Docker Socket Args

### What I Changed

Removed:

```groovy
args '-v /var/run/docker.sock:/var/run/docker.sock -e HOME=/tmp'
```

### What Happened

- Initial build surprisingly passed
- After full args removal + restart:
  pipeline failed

### Key Learning

Important distinction:

- Jenkins controller launches Docker containers
- Socket mount is only required INSIDE build container for Docker access

This clarified:
- controller-side Docker access
- vs
- in-container Docker access

---

# 🧩 Problems Faced & Fixes

| Problem | Root Cause | Fix |
|---|---|---|
| Permission denied on docker.sock | Jenkins user missing docker group | Added jenkins user to docker group |
| pytest command not found | PATH issue | Exported `/tmp/.local/bin` |
| pip permission issues | Non-root container | Used `pip install --user` |
| Build failed after args removal | Missing env configuration | Restored args line |

---

# 📊 Build Verification

Successfully verified:

✅ Docker image pull  
✅ Container-based execution  
✅ Python execution inside container  
✅ pytest execution  
✅ JUnit report publishing  
✅ Container destruction after build  

---

# 📸 Screenshots

## ✅ Successful Build
<img width="1272" height="605" alt="build-passed" src="https://github.com/user-attachments/assets/ae4fe361-f92b-4f15-8484-bac7d8ddc329" />   

---

## 📄 JUnit Test Results

<img width="1272" height="306" alt="junit-results" src="https://github.com/user-attachments/assets/66320769-addc-4be5-a957-7259acb54113" />   

---

## 🐳 Docker Container Lifecycle Proof

<img width="1272" height="667" alt="container-lifecycle" src="https://github.com/user-attachments/assets/fc7105a0-704f-4e49-ac48-d9d192789bfb" />   

---

## ❌ Break Exercise 1 — Wrong Image

<img width="1272" height="449" alt="break-it-1-wrong-image" src="https://github.com/user-attachments/assets/b3940423-bec4-4fd9-ba9b-cb20dbe5e7a5" />   

---

## ❌ Break Exercise 2 — Removed Args

<img width="1272" height="399" alt="break-it-2-no-socket" src="https://github.com/user-attachments/assets/425a5ea4-2906-4afa-b5d3-bd6f68af72d2" />   

---

# 📋 Lab Completion Checklist

## Setup

- [x] Docker socket mounted
- [x] Jenkins connected to Docker daemon
- [x] Docker image verified

## Pipeline

- [x] Jenkinsfile created
- [x] Docker agent configured
- [x] pytest integrated
- [x] JUnit reporting enabled

## Validation

- [x] Build passed
- [x] Tests executed
- [x] Reports archived
- [x] Container lifecycle verified

## Break-It Exercises

- [x] Wrong image failure tested
- [x] Docker args removal tested
- [x] Full lifecycle proof pending

---

# 🎤 Interview Talking Points

## 🔹 Why Docker Agents?

Docker agents provide:

- Clean execution environments
- Better scalability
- Dependency isolation
- Reduced maintenance
- Reproducible builds

---

## 🔹 Why Avoid `latest` Tag?

Using `latest` introduces unpredictability.

Production pipelines should always use pinned versions:

✅ Good:

```groovy
image 'python:3.11-slim'
```

❌ Bad:

```groovy
image 'python:latest'
```

---

## 🔹 Why Is This Important in Modern DevOps?

This lab demonstrates concepts used in:

- Kubernetes-based Jenkins agents
- GitHub Actions runners
- GitLab CI runners
- Tekton pipelines
- Cloud-native CI/CD systems

Modern CI/CD platforms heavily rely on ephemeral infrastructure.

---

# 📚 Key Learnings

This lab helped me understand:

- Ephemeral infrastructure
- Jenkins Docker internals
- Docker socket behavior
- CI/CD reproducibility
- Runtime isolation
- Container lifecycle management
- Production-style Jenkins pipelines

---

# 🚀 My Biggest Takeaway

> Static agents solve CI/CD execution.
>
> Ephemeral Docker agents solve scalability, reliability, reproducibility, and operational maintenance.

---

# ✍️ Author

**[Himanshu Kumar](https://www.linkedin.com/in/h1manshu-kumar/)** - Learning by building, documenting, and sharing 🚀   

------------------------------------------------------------------------

🔥 *Built with a focus on real DevOps engineering practices, not just
theory.*

---

<div align="center">

## ⭐ If you found this useful, consider starring the repository ⭐

</div>
