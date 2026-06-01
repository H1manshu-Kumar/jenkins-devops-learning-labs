# 🚀 Lab 3.3 - Multi-Agent Jenkins Pipeline (Distributed Builds)

<div align="center">

![Jenkins](https://img.shields.io/badge/Jenkins-Multi--Agent-red?style=for-the-badge\&logo=jenkins)
![Docker](https://img.shields.io/badge/Docker-Ephemeral%20Agent-blue?style=for-the-badge\&logo=docker)
![Linux](https://img.shields.io/badge/Linux-Static%20Agent-black?style=for-the-badge\&logo=linux)
![Pytest](https://img.shields.io/badge/Pytest-Validation-green?style=for-the-badge\&logo=pytest)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)

</div>

---

# 📌 Overview

In previous labs, builds executed on a single agent.

In this lab, I built a **distributed Jenkins pipeline** where different stages execute on different agents based on their responsibilities.

The pipeline uses:

* A Linux static agent for build preparation
* An ephemeral Docker agent for validation and testing
* Artifact transfer using Jenkins `stash` and `unstash`
* Controller-safe execution using `agent none`

This simulates how modern enterprise Jenkins environments distribute workloads across specialized execution nodes.

---

# 🎯 Learning Objectives

By completing this lab, I learned how to:

✅ Use multiple agents within a single pipeline

✅ Route stages to specific agents using labels

✅ Use `agent none` for controller-safe execution

✅ Transfer files between agents using `stash` and `unstash`

✅ Understand workspace isolation across agents

✅ Execute tests inside ephemeral Docker containers

✅ Publish JUnit reports from distributed builds

✅ Troubleshoot agent scheduling issues

✅ Understand how large Jenkins environments scale build execution

---

# 🧠 Core Concept — Distributed Build Execution

A Jenkins Controller should coordinate work.

It should not perform work.

Modern Jenkins environments distribute execution across multiple agents.

```text
                         Jenkins Controller
                                 │
                                 │
                          Schedules Work
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                                              │
          ▼                                              ▼

    Linux Static Agent                         Docker Agent
    (Persistent Node)                     (Ephemeral Container)

    Checkout Code                         Validate Artifact
    Create Artifact                       Run Tests
    Stash Files                           Generate Reports

          │                                              │
          └─────────────── Artifact Transfer ────────────┘
```

---

# 🏗️ Architecture Overview

```text
┌─────────────────────────────────────────────┐
│              Jenkins Controller             │
│                                             │
│  Reads Jenkinsfile                          │
│  Schedules Stages                           │
│  Transfers Stashed Artifacts                │
│  Publishes Reports                          │
│                                             │
│  Does NOT execute build logic               │
└─────────────────┬───────────────────────────┘
                  │
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼

┌──────────────────┐   ┌──────────────────────┐
│   Linux Agent    │   │    Docker Agent      │
│ label:           │   │ python:3.11-slim     │
│ linux-agent      │   │                      │
│                  │   │                      │
│ Checkout         │   │ Unstash Artifact     │
│ Create Artifact  │   │ Run pytest           │
│ Stash Artifact   │   │ Generate JUnit XML   │
└──────────────────┘   └──────────────────────┘
```

---

# 🧪 QA → DevOps Mapping

| QA Mindset               | DevOps Equivalent              |
| ------------------------ | ------------------------------ |
| Selenium Grid Hub        | Jenkins Controller             |
| Selenium Grid Node       | Jenkins Agent                  |
| Test Environment Routing | Agent Labels                   |
| Test Artifact Sharing    | stash/unstash                  |
| Parallel Test Execution  | Distributed Pipeline Execution |
| Fresh Browser Session    | Ephemeral Docker Agent         |
| Test Report Collection   | JUnit Publishing               |

---

# ⚙️ Tech Stack Used

| Tool        | Purpose                    |
| ----------- | -------------------------- |
| Jenkins     | CI/CD Orchestration        |
| Linux Agent | Static Build Node          |
| Docker      | Ephemeral Test Environment |
| Python 3.11 | Runtime Environment        |
| pytest      | Validation Framework       |
| JUnit XML   | Jenkins Reporting          |
| Git         | Source Control             |

---

# 📂 Project Structure

```text
phase-3-agents/
└── lab-3.3-multi-agent/
    ├── README.md
    ├── Jenkinsfile
    ├── setup-notes.md
    │
    ├── build/
    │   └── app.txt
    │
    ├── results/
    │   └── test-results.xml
    │
    ├── tests/
    │   └── test_artifact.py
    │
    └── screenshots/
        ├── successful-build.png
        ├── linux-agent-stage.png
        ├── docker-agent-stage.png
        ├── stash-unstash-proof.png
        ├── junit-results.png
        ├── break-it-1.png
        ├── break-it-2.png
        └── break-it-3.png
```

---

# 🔄 Pipeline Flow

```text
Stage 1
Linux Agent
│
├── Checkout Code
├── Create Artifact
└── Stash Artifact

          │
          ▼

Stage 2
Docker Agent
│
├── Unstash Artifact
├── Validate Artifact
├── Run Pytest
├── Generate JUnit XML
└── Stash Results

          │
          ▼

Stage 3
Linux Agent
│
├── Unstash Results
├── Archive Reports
└── Publish Build Output
```

---

# 🏆 Final Jenkinsfile Used

```groovy
pipeline {

    agent none

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {

        stage('Build - Linux Agent') {

            agent {
                label 'linux-agent'
            }

            steps {

                echo "Running on Linux Agent"

                sh '''
                    mkdir -p build

                    echo "Application Build Artifact" > build/app.txt

                    echo "Hostname: $(hostname)"
                    echo "Node Name: ${NODE_NAME}"

                    cat build/app.txt
                '''

                stash name: 'build-artifact',
                      includes: 'build/**'
            }
        }

        stage('Validate - Docker Agent') {

            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }

            steps {

                unstash 'build-artifact'

                sh '''
                    mkdir -p results

                    pip install --user pytest

                    export PATH=/tmp/.local/bin:$PATH

                    ls -la build/

                    cat build/app.txt
                '''

                writeFile file: 'tests/test_artifact.py', text: '''
from pathlib import Path

def test_artifact_exists():
    assert Path("build/app.txt").exists()

def test_artifact_content():
    content = Path("build/app.txt").read_text()
    assert "Application Build Artifact" in content
'''

                sh '''
                    export PATH=/tmp/.local/bin:$PATH

                    pytest tests/test_artifact.py \
                    --junit-xml=results/test-results.xml \
                    -v
                '''

                stash name: 'test-results',
                      includes: 'results/**'
            }
        }

        stage('Archive - Linux Agent') {

            agent {
                label 'linux-agent'
            }

            steps {

                unstash 'test-results'

                sh '''
                    echo "Results received from Docker Agent"
                    ls -la results/
                '''
            }
        }
    }

    post {

        always {

            junit 'results/test-results.xml'

            archiveArtifacts(
                artifacts: 'build/**',
                fingerprint: true
            )
        }

        success {
            echo 'SUCCESS - Multi-Agent Pipeline Completed'
        }

        failure {
            echo 'FAILURE - Check Pipeline Logs'
        }
    }
}
```

---

# 🔥 Key Features Implemented

✅ Controller-safe execution with `agent none`

✅ Linux static agent execution

✅ Docker agent execution

✅ Stage-level agent routing

✅ Artifact transfer using stash

✅ Artifact retrieval using unstash

✅ Pytest validation

✅ JUnit reporting

✅ Build retention policy

✅ Pipeline timeout protection

✅ Distributed build architecture

---

# 💥 Break-It Exercises Completed

---

## ❌ Exercise 1 — Remove Stash

### What I Changed

```groovy
stash name: 'build-artifact'
```

removed completely.

### What Happened

```text
No such saved stash 'build-artifact'
```

### Key Learning

Agents do not share workspaces automatically.

Artifact transfer requires:

```groovy
stash
unstash
```

---

## ❌ Exercise 2 — Wrong Agent Label

### What I Changed

```groovy
label 'linux-agent'
```

to

```groovy
label 'prod-linux'
```

### What Happened

```text
Still waiting to schedule task
```

Pipeline remained queued.

### Key Learning

Agent labels must match available nodes.

---

## ❌ Exercise 3 — Remove agent none

### What I Changed

```groovy
agent none
```

to

```groovy
agent any
```

### What Happened

Controller executor became eligible for pipeline execution.

### Key Learning

Controllers should orchestrate.

Agents should execute.

---

# 🧩 Problems Faced & Fixes

| Problem                          | Root Cause          | Fix                     |
| -------------------------------- | ------------------- | ----------------------- |
| Artifact missing in Docker stage | Workspace isolation | stash/unstash           |
| Pipeline stuck in queue          | Incorrect label     | Corrected label         |
| pytest not found                 | PATH issue          | Exported PATH           |
| JUnit report missing             | Wrong report path   | Corrected file location |
| Build executed unexpectedly      | Missing agent none  | Added agent none        |

---

# 📊 Build Verification

Successfully verified:

✅ Linux Agent execution

✅ Docker Agent execution

✅ Artifact creation

✅ Artifact transfer

✅ Workspace isolation

✅ Pytest execution

✅ JUnit reporting

✅ Multi-agent scheduling

---

# 🎤 Interview Talking Points

## 🔹 Why Use agent none?

Using:

```groovy
agent none
```

prevents accidental controller execution.

Benefits:

* Better scalability
* Better security
* Explicit agent assignment
* Production best practice

---

## 🔹 What Problem Does stash/unstash Solve?

Different agents have different workspaces.

Files do not automatically move between them.

`stash` and `unstash` allow Jenkins to transfer files between stages running on different agents.

---

## 🔹 Why Use Different Agents For Different Stages?

Different stages may require:

* Different operating systems
* Different runtimes
* Different tools
* Different resource requirements

Distributed execution improves scalability and efficiency.

---

## 🔹 What Happens If No Agent Matches A Label?

Jenkins cannot schedule the build.

Pipeline remains queued until a matching node becomes available.

---

## 🔹 Why Is This Important In Real DevOps?

This architecture is commonly used in:

* Enterprise Jenkins installations
* Kubernetes Jenkins agents
* GitHub Actions runners
* GitLab runners
* Cloud-native CI/CD platforms

---

# 📚 Key Learnings

This lab helped me understand:

* Distributed build execution
* Agent scheduling
* Workspace isolation
* Artifact movement between agents
* Controller best practices
* Stage-level execution environments
* Enterprise Jenkins architecture

---

# 🚀 Biggest Takeaway

> A Jenkins Controller should coordinate builds.
>
> Jenkins Agents should execute builds.
>
> Multi-agent pipelines allow the right work to run in the right environment while keeping the controller lightweight, secure, and scalable.

---

# 📋 Lab Completion Checklist

## Setup

* [x] Linux agent available
* [x] Docker agent configured
* [x] agent none configured

## Pipeline

* [x] Stage-level agents configured
* [x] stash implemented
* [x] unstash implemented
* [x] pytest integrated
* [x] JUnit reporting enabled

## Validation

* [x] Build artifact created
* [x] Artifact transferred
* [x] Tests executed
* [x] Reports published

## Break-It Exercises

* [x] Missing stash tested
* [x] Wrong label tested
* [x] agent none validation completed

---

# ✍️ Author

**Himanshu Kumar** - Learning DevOps by building, breaking, documenting, and sharing 🚀

---

🔥 *This lab demonstrates one of the most important concepts in Jenkins: distributed build execution using multiple agents.*

