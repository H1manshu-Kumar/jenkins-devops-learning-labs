# Lab 3.2 - Docker Agent (Ephemeral Container Builds)

> **Phase:** 3 — Jenkins Agents + Distributed Builds
> **Lab:** 3.2 of 4
> **Status:** ⏳ In Progress
> **Started:** <!-- Add your start date -->
> **Completed:** <!-- Add your completion date -->

---

## Objective

Replace the static SSH agent from Lab 3.1 with an **ephemeral Docker agent**.
Every build gets a fresh container. Container dies after the build completes.

By the end of this lab:
- Jenkins spins up a Docker container as an agent per build
- Build runs inside `python:3.11-slim` container
- Container is destroyed automatically after build completes
- pytest results are published via `junit` post step
- You can prove the container lifecycle from console logs

---

## Concept First — What Is an Ephemeral Docker Agent?

```
Lab 3.1 — Static Agent                 Lab 3.2 — Docker Agent
──────────────────────────────────────────────────────────────
Container runs 24/7                     Container spins up per build
Manual restart when it crashes          Nothing to restart — gone after build
Disk fills up over time                 Clean slate every run
SSH connection                          Docker socket connection
Pre-installed dependencies              Fresh image every time
One agent serves all builds             One container per build
```

### How Docker Agent Works Under the Hood

```
┌─────────────────────────────────────────────┐
│             Jenkins Controller              │
│                                             │
│  1. Build triggered                         │
│  2. Reads: agent { docker { image '...' } } │
│  3. Calls Docker socket                     │
│  4. Docker spins up container               │
│  5. Build runs inside container             │
│  6. Results sent back to controller         │
│  7. Container destroyed                     │
│                                             │
│  /var/run/docker.sock ← mounted from host   │
└──────────────────┬──────────────────────────┘
                   │
         Docker socket call
         (not SSH this time)
                   │
┌──────────────────▼──────────────────────────┐
│         python:3.11-slim Container          │
│                                             │
│  - Spins up when build starts               │
│  - Runs pipeline stages                     │
│  - Publishes test results                   │
│  - Destroyed when build ends                │
│  - Leaves zero state behind                 │
└─────────────────────────────────────────────┘
```

### Why Docker Socket Mounting Matters

The Jenkins controller needs to talk to Docker to spin up agent containers.
It does this via `/var/run/docker.sock` — the Docker daemon socket on the host.

```
Host Machine
  └── /var/run/docker.sock         ← Docker daemon lives here
        ↑
        mounted into controller at:
        └── /var/run/docker.sock   ← controller uses this to call Docker API
              ↓
              docker run python:3.11-slim ← agent container spun up on host
```

Your controller already has this mounted — confirmed in pre-check.

---

## QA-to-DevOps Mapping

| QA Concept | Lab 3.2 Equivalent |
|---|---|
| Clean browser session per test | Fresh Docker container per build |
| No leftover cookies/cache between tests | No leftover files between builds |
| Selenium container in docker-compose | python:3.11-slim agent container |
| Test isolation | Build isolation |
| teardown() after each test | Container destroyed after each build |

Your QA instinct — tests should run in isolation and leave no side effects —
is exactly the principle behind ephemeral Docker agents.

---

## Actual Setup Used in This Lab

```
OS                 Ubuntu / Debian (host machine)
Controller         jenkins/jenkins:lts → jenkins-controller
Docker Socket      /var/run/docker.sock (mounted in controller)
Agent Type         Ephemeral Docker container (not static)
Agent Image        python:3.11-slim
Plugin             Docker Pipeline (already installed)
Jenkins UI Port    8181
```

---

## Folder Structure

```
phase-3-agents/
└── lab-3.2-docker-agent/
    ├── README.md                          ← You are here
    ├── setup-notes.md                     ← Every command run with actual output
    ├── Jenkinsfile                        ← Pipeline using Docker agent
    ├── tests/
    │   └── test_sample.py                 ← pytest test file run inside container
    └── screenshots/
        ├── build-passed.png               ← Successful build console log
        ├── container-lifecycle.png        ← Container up during build, gone after
        ├── junit-results.png              ← Test results published in Jenkins UI
        ├── break-it-1-wrong-image.png     ← Wrong Docker image error
        ├── break-it-2-no-socket.png       ← Docker socket missing error
        └── break-it-3-lifecycle-proof.png ← Container gone after build proof
```

---

## Pre-Lab Checklist

```
[x] Jenkins controller running → curl http://localhost:8181
[x] Docker socket mounted in controller
    → docker inspect jenkins-controller | grep -i sock
    → shows /var/run/docker.sock:/var/run/docker.sock

[x] Docker Pipeline plugin installed
    → Manage Jenkins → Plugins → Installed → search: Docker Pipeline

[x] python:3.11-slim image available on host
    → docker pull python:3.11-slim
    → docker images | grep python

[ ] Verify Jenkins can call Docker
    → Step 1 of this lab confirms this via first build
```

---

## Step-by-Step Lab Guide

### Step 1 — Verify Jenkins Can Access Docker Socket

Before writing any pipeline, confirm the controller can actually use Docker.

```bash
# Run a test Docker command from inside the controller container
docker exec jenkins-controller docker ps

# Expected output: list of running containers (same as your host docker ps)
# If you see: "permission denied" → jump to the fix below
# If you see: container list → you are good to go
```

**If you get permission denied:**
```bash
# Check the docker group ID on your host
getent group docker

# Add jenkins user to docker group inside controller
docker exec -u root jenkins-controller usermod -aG docker jenkins

# Restart the controller container
docker restart jenkins-controller

# Test again
docker exec jenkins-controller docker ps
```

---

### Step 2 — Write the Test File

This is the Python test that will run inside the Docker agent container.

Create `phase-3-agents/lab-3.2-docker-agent/tests/test_sample.py`:

```python
# Simple pytest file — runs inside python:3.11-slim container
# Proves that the Docker agent has Python and can run tests


def test_addition():
    """Basic math — proves Python is working inside container."""
    assert 1 + 1 == 2


def test_string_operations():
    """String test — proves standard library is available."""
    name = "devops"
    assert name.upper() == "DEVOPS"
    assert len(name) == 6


def test_list_operations():
    """List test — proves basic Python data structures work."""
    items = ["jenkins", "docker", "python"]
    assert len(items) == 3
    assert "docker" in items


def test_environment_is_clean():
    """Proves each build starts fresh — no leftover state."""
    import os
    import tempfile

    # Create a temp file
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp_path = temp.name
    temp.close()

    # Verify it was created
    assert os.path.exists(temp_path)

    # Clean it up
    os.remove(temp_path)
    assert not os.path.exists(temp_path)
```

---

### Step 3 — Write the Jenkinsfile

Create `phase-3-agents/lab-3.2-docker-agent/Jenkinsfile`:

```groovy
pipeline {
    // No static agent — Docker spins up a fresh container per build
    // python:3.11-slim is pulled from Docker Hub if not cached locally
    agent {
        docker {
            image 'python:3.11-slim'
            // Mount Docker socket so container can call Docker if needed
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    options {
        // Keep last 5 builds only — good practice
        buildDiscarder(logRotator(numToKeepStr: '5'))
        // Fail build if it runs longer than 10 minutes
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        stage('Verify - Docker Agent Environment') {
            steps {
                // Prove WHERE and WHAT this build is running on
                sh 'echo "Hostname: $(hostname)"'
                sh 'echo "Whoami: $(whoami)"'
                sh 'echo "Python version: $(python3 --version)"'
                sh 'echo "Working dir: $(pwd)"'
                sh 'echo "Build number: ${BUILD_NUMBER}"'
                sh 'echo "Node Name: ${NODE_NAME}"'
            }
        }

        stage('Install Dependencies') {
            steps {
                // pip install runs fresh every build — clean environment
                sh 'pip install pytest --quiet'
                sh 'pip show pytest | grep Version'
            }
        }

        stage('Run Tests') {
            steps {
                // Run pytest and output JUnit XML — Jenkins reads this format natively
                sh '''
                    pytest tests/test_sample.py \
                        --junit-xml=results/test-results.xml \
                        --verbose \
                        -p no:cacheprovider
                '''
            }
        }

        stage('Verify - Container Will Be Destroyed') {
            steps {
                // Print container ID — you will confirm this is gone after build
                sh 'echo "Container ID: $(hostname)"'
                sh 'echo "This container will not exist after this build completes"'
            }
        }
    }

    post {
        always {
            // Publish test results BEFORE container is destroyed
            // Jenkins reads the XML and stores results on controller
            junit 'results/test-results.xml'

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

### Step 4 — Create Results Directory

The Jenkinsfile writes test results to `results/` — Jenkins needs this to exist.

Add a `.gitkeep` so the folder is tracked in Git:

```bash
mkdir -p phase-3-agents/lab-3.2-docker-agent/results
touch phase-3-agents/lab-3.2-docker-agent/results/.gitkeep
```

Add `results/*.xml` to `.gitignore` — generated files should not be committed:

```bash
echo "phase-3-agents/lab-3.2-docker-agent/results/*.xml" >> .gitignore
```

---

### Step 5 — Commit and Push

```bash
git add phase-3-agents/lab-3.2-docker-agent/
git add .gitignore
git commit -m "feat(lab-3.2): add Docker agent Jenkinsfile and pytest test file"
git push origin feat/phase-3-agents
```

---

### Step 6 — Create Pipeline Job in Jenkins

```
Jenkins UI → New Item
Name:   lab-3.2-docker-agent
Type:   Pipeline → OK

Pipeline section:
  Definition:  Pipeline script from SCM
  SCM:         Git
  URL:         your repo URL
  Branch:      */feat/phase-3-agents
  Script path: phase-3-agents/lab-3.2-docker-agent/Jenkinsfile

→ Save → Build Now
```

**What to watch in console log:**
```
- "Pulling docker image python:3.11-slim"     ← Docker agent spinning up
- "Running on Jenkins in /var/jenkins/..."    ← Build inside container
- hostname = container ID (short hash)        ← NOT agent-01, NOT controller
- Python 3.11.x                               ← Correct image confirmed
- pytest output with PASSED tests             ← Tests running inside container
- "Archiving test results"                    ← Results saved before container dies
- Container ID printed in last stage          ← Note this for break-it exercise 3
```

---

### Step 7 — Verify Test Results in Jenkins UI

```
Jenkins UI → lab-3.2-docker-agent → Last build
→ Test Result link should appear on build page
→ Shows: X tests, 0 failures, 0 skipped
→ Click through to see individual test names
```

This proves: results were captured and stored on the controller
before the container was destroyed.

---

### Step 8 — Break-It Exercises

#### Exercise 1 — Wrong Docker Image Name

```
What to do:
- Change image in Jenkinsfile from 'python:3.11-slim' to 'python:nonexistent-tag'
- Commit: break(lab-3.2): use wrong Docker image to observe pull failure
- Trigger build

What to observe:
- Does it fail immediately or queue silently?
- What is the exact error message in console log?
- How is this different from the wrong label behaviour in Lab 3.1?

Fix:
- Restore image to 'python:3.11-slim'
- Commit: fix(lab-3.2): restore correct Docker image tag
- Confirm build passes
```

---

#### Exercise 2 — Remove Docker Socket Mount

```
What to do:
- Remove the args line from Jenkinsfile:
  args '-v /var/run/docker.sock:/var/run/docker.sock'
- Commit: break(lab-3.2): remove docker socket args to observe impact
- Trigger build

What to observe:
- Does the build still pass? (it likely will — socket arg is optional here)
- When IS the socket arg needed?
- Document what changes in the console log

Fix:
- Restore the args line
- Commit: fix(lab-3.2): restore docker socket args
```

---

#### Exercise 3 — Verify Container Lifecycle

```
What to do:
- Note the container ID printed in the last stage of the build
- While build is running: docker ps | grep python
  You should see the container running

- After build completes: docker ps | grep python
  Container should be gone — destroyed automatically

What to screenshot:
- docker ps during build showing python container running
- docker ps after build showing it is gone
- Console log showing the container ID that no longer exists

This is the key proof of ephemeral behaviour.
```

---

## Lab Completion Checklist

```
Setup
[ ] Docker socket confirmed mounted in jenkins-controller
[ ] Jenkins controller can run: docker exec jenkins-controller docker ps
[ ] python:3.11-slim image available on host

Pipeline
[ ] tests/test_sample.py created with 4 tests
[ ] Jenkinsfile created using agent { docker { image 'python:3.11-slim' } }
[ ] results/.gitkeep added — results/*.xml in .gitignore
[ ] Pipeline job created in Jenkins pointing to Jenkinsfile

Build Verification
[ ] First build triggered and passed
[ ] Console log shows Docker image being pulled/used
[ ] Console log shows Python version inside container
[ ] pytest output shows all 4 tests passed
[ ] Test results visible in Jenkins UI (junit report)
[ ] Container ID in log confirmed gone after build (docker ps)

Break-It Exercises
[ ] Exercise 1 — Wrong image — error documented, fixed
[ ] Exercise 2 — Socket args removed — behaviour documented, fixed
[ ] Exercise 3 — Container lifecycle proven with docker ps screenshots

Documentation
[ ] setup-notes.md filled with every command and output
[ ] README status updated to Completed
[ ] Screenshots added to screenshots/ folder
[ ] INTERVIEW-PREP.md updated with Lab 3.2 talking points
```

---

## Troubleshooting Guide

| Problem | Likely Cause | Fix |
|---|---|---|
| "permission denied on docker.sock" | Jenkins user not in docker group | `docker exec -u root jenkins-controller usermod -aG docker jenkins` then restart |
| "Cannot connect to Docker daemon" | Socket not mounted in controller | Recreate controller with `-v /var/run/docker.sock:/var/run/docker.sock` |
| "image not found" or pull error | Wrong image tag or no internet | Verify tag on Docker Hub, check `docker pull` manually |
| Build passes but no test results | results/ dir missing or wrong path | Check `mkdir -p results` runs before pytest |
| Container still running after build | Build failed mid-way — container orphaned | `docker ps | grep python` then `docker stop <id>` |
| pytest not found | pip install stage failed | Check pip install logs, verify image has pip |
| junit step fails | XML not generated | Check pytest ran successfully before post block |

---

## Interview Talking Points

**Q: What is the difference between a static agent and a Docker agent?**
Static agent is a long-lived container that stays running between builds.
Docker agent is ephemeral — spins up per build, destroyed after.
Docker agents give clean environment every run, no disk buildup,
no dependency conflicts between builds. Trade-off: slight startup
overhead per build for pulling and starting the container.

**Q: How does Jenkins spin up a Docker container as an agent?**
Jenkins controller uses the Docker socket mounted at /var/run/docker.sock.
This lets the controller call the Docker API on the host machine.
When a build starts, Jenkins runs `docker run` with the specified image,
executes pipeline stages inside it, then destroys it after the post block.

**Q: What happens to test results when the Docker agent container is destroyed?**
The `junit` post step runs before the container is destroyed.
Jenkins reads the XML file and stores results on the controller.
So even after the container is gone, results are preserved and
visible in the Jenkins UI under the build's Test Result page.

**Q: Why is ephemeral Docker agent preferred over static agent in production?**
Four reasons:
- Clean environment every build — no leftover state from previous builds
- No agent maintenance — no SSH keys, no manual restarts, no disk cleanup
- Dependency isolation — each pipeline can use a different image/version
- Scale to zero — no idle agent consuming resources between builds

**Q: What does pinning to `latest` Docker image cause in pipelines?**
Upstream image updates silently break your build.
A Monday build passes on python:latest 3.11. Tuesday it updates to 3.12.
Your code breaks with zero changes on your end.
Always pin to specific tags: python:3.11-slim not python:latest.

**Q: How do you publish test results from inside an ephemeral container?**
Use the `junit` step in the `post { always { } }` block.
This ensures results are archived even if the build fails.
The XML file is read by Jenkins and stored on the controller
before the container is torn down.

---

## My Learnings — Lab 3.2 Retrospective

> Fill this section before raising the PR.

### What I Built

### What Was Different From Lab 3.1

### What Broke and How I Fixed It

### What Was Confusing Before I Built It

### Key Command That Saved Me

### What I Would Do Differently

---

## References

- [Docker Pipeline Plugin Docs](https://plugins.jenkins.io/docker-workflow/)
- [Jenkins Pipeline — agent docker syntax](https://www.jenkins.io/doc/book/pipeline/syntax/#agent)
- [python:3.11-slim on Docker Hub](https://hub.docker.com/_/python)
- [pytest JUnit XML output](https://docs.pytest.org/en/stable/how-to/output.html)

---

*Part of [Phase 3 — Agents](../README.md) | [Jenkins DevOps Learning Labs](../../README.md)*
