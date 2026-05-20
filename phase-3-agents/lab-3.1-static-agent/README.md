# Lab 3.1 — Static Agent Setup   

> **Phase:** 3 — Jenkins Agents + Distributed Builds   
> **Lab:** 3.1 of 4   
> **Status:** ✅ Completed   

---

## 🎯 Objective

Connect a **permanent SSH-based agent** to your Jenkins controller.
Verify that builds run on the agent — not the controller.

By the end of this lab:
- Jenkins controller and agent run as separate Docker containers
- They communicate over a shared Docker network
- A pipeline explicitly targets the agent by label
- You can prove the build ran on the agent (not controller) from console logs

---

## 🧠 Concept First — What Is a Static Agent?

A **static agent** (also called a permanent agent or node) is a long-lived machine that stays connected to the Jenkins controller and waits for builds to be assigned to it.

```
┌─────────────────────────────────────────┐
│           Jenkins Controller            │
│                                         │
│  - Manages jobs, pipelines, schedules   │
│  - Decides which agent gets the build   │
│  - NEVER runs the build itself          │
│                                         │
│  Port 8080  →  Web UI                   │
│  Port 50000 →  Agent communication      │
└──────────────────┬──────────────────────┘
                   │
          SSH connection
          (Port 22)
                   │
┌──────────────────▼──────────────────────┐
│            Static Agent                 │
│                                         │
│  - Receives build instructions          │
│  - Executes pipeline stages             │
│  - Stores workspace files               │
│  - Reports results back to controller   │
└─────────────────────────────────────────┘
```

### Why SSH for Static Agents?

Jenkins supports multiple ways to connect agents:
- **SSH** — Controller initiates connection to agent. Most common for permanent agents.
- **JNLP/WebSocket** — Agent initiates connection to controller. Used when agent is behind firewall.
- **Docker** — Covered in Lab 3.2.

In this lab you use **SSH** — it is the most common pattern in enterprise environments.

---

## 🔗 QA-to-DevOps Mapping

| QA Concept | Lab 3.1 Equivalent |
|-----------|-------------------|
| Selenium Grid Hub | Jenkins Controller |
| Selenium Grid Node | Static Agent |
| Node registration in Grid | Agent connected via SSH |
| Test routed to specific node | Build routed via agent label |
| Node stays running between tests | Agent stays connected between builds |

The mental model is identical. The implementation layer is different.

---

## ⚙️ Your Setup Context

```
OS             Ubuntu / Debian
Jenkins        Running as Docker container (docker run)
Agent          Will run as a separate Docker container
Network        Custom Docker bridge network (jenkins-net)
Communication  SSH between controller and agent containers
```

---

## 📂 Folder Structure

```
phase-3-agents/
└── lab-3.1-static-agent/
    ├── README.md              ← You are here
    ├── setup-notes.md         ← Every command you ran (fill as you go)
    ├── Jenkinsfile            ← Pipeline that targets the agent by label
    └── screenshots/           ← Agent connected, build console log proof
        ├── break-it-1-queue-stuck.png
        └── break-it-1-no-node-error.png
        └── break-it-1-build-passed-after-fix.png
        └── break-it-2-agent-red-x.png
        └── break-it-2-queue-blocked.png
        └── break-it-2-agent-log-error.png
        └── break-it-2-agent-fix.png
        └── exercise-3-docker-ps-container-ids.png
        └── exercise-3-console-log-hostname-proof.png
        └── exercise-3-nodes-agent-connected.png
        

```

---

## 🔑 Pre-Lab Checklist

Before starting — verify these are true:

```
[x] Jenkins container is running
    → curl http://localhost:8080  should return Jenkins UI

[x] Docker is installed and working
    → docker ps  should show your Jenkins container

[x] You know your Jenkins container name
    → docker ps --format "{{.Names}}"

[x] Port 50000 is exposed on your Jenkins container
    → docker inspect <container-name> | grep 50000
    → If NOT exposed, you will need to recreate the container (steps below)
```

### If Port 50000 Is Not Exposed — Recreate Jenkins Container

```bash
# Stop and remove existing container (your data is safe if you used a volume)
docker stop <your-jenkins-container>
docker rm <your-jenkins-container>

# Recreate with both ports exposed
docker run -d \
  --name jenkins \
  --network jenkins-net \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts

# Verify both ports are mapped
docker ps
# Should show: 0.0.0.0:8080->8080/tcp, 0.0.0.0:50000->50000/tcp
```

---

## 📋 Step-by-Step Lab Guide

### Step 1 — Create a Docker Network

Both containers (controller + agent) must be on the same Docker network
so they can resolve each other by container name.

```bash
# Create a dedicated network for Jenkins
docker network create jenkins-net

# Verify it was created
docker network ls | grep jenkins-net
```

**Connect your existing Jenkins controller to this network:**

```bash
docker network connect jenkins-net <your-jenkins-container-name>

# Verify controller is on the network
docker network inspect jenkins-net
# You should see your Jenkins container listed under "Containers"
```

---

### Step 2 — Generate SSH Key Pair

The controller uses a private key to SSH into the agent.
The agent holds the matching public key.

```bash
# Generate key pair on your host machine
# Do NOT set a passphrase — press Enter when asked
ssh-keygen -t rsa -b 4096 -C "jenkins-agent" -f ~/.ssh/jenkins-agent

# Verify both keys were created
ls -la ~/.ssh/jenkins-agent*
# Should show:
# jenkins-agent      ← private key (goes into Jenkins credentials)
# jenkins-agent.pub  ← public key (goes into agent container)

# View the public key — you will need this in Step 3
cat ~/.ssh/jenkins-agent.pub

# View the private key — you will need this in Step 4
cat ~/.ssh/jenkins-agent
```

---

### Step 3 — Run the Agent Container

```bash
# Run jenkins/ssh-agent image with your public key injected
docker run -d \
  --name jenkins-agent-01 \
  --network jenkins-net \
  -e "JENKINS_AGENT_SSH_PUBKEY=$(cat ~/.ssh/jenkins-agent.pub)" \
  jenkins/ssh-agent:latest

# Verify agent container is running
docker ps | grep jenkins-agent-01

# Verify agent is on the jenkins-net network
docker network inspect jenkins-net
# Both jenkins and jenkins-agent-01 should be listed

# Test SSH connectivity from host (optional sanity check)
docker exec jenkins-agent-01 hostname
# Should print the container ID — confirms container is alive
```

---

### Step 4 — Add SSH Private Key to Jenkins Credentials

```
Jenkins UI → Manage Jenkins → Credentials
         → System → Global credentials → Add Credentials

Kind:         SSH Username with private key
Scope:        Global
ID:           jenkins-agent-ssh-key        ← you will reference this in node config
Description:  SSH key for static agent 01
Username:     jenkins                      ← default user in jenkins/ssh-agent image

Private Key:  Enter directly
              → Paste the ENTIRE private key including header and footer:
                -----BEGIN RSA PRIVATE KEY-----
                ...
                -----END RSA PRIVATE KEY-----
```

**Get your private key content:**
```bash
cat ~/.ssh/jenkins-agent
# Copy everything including the BEGIN and END lines
```

---

### Step 5 — Register the Agent in Jenkins

```
Jenkins UI → Manage Jenkins → Nodes → New Node

Node name:          agent-01
Type:               Permanent Agent → OK

Description:        Static Docker agent for builds
Number of executors: 2
Remote root dir:    /home/jenkins/agent
Labels:             linux-agent               ← THIS is how you target it in Jenkinsfile
Usage:              Only build jobs with label expressions matching this node

Launch method:      Launch agents via SSH

Host:               jenkins-agent-01          ← container name (resolves via jenkins-net)
Credentials:        jenkins-agent-ssh-key     ← the credential you created in Step 4
Host Key Verification Strategy: Non verifying  ← for learning only

→ Save
```

**Wait 30-60 seconds then verify:**
```
Manage Jenkins → Nodes
→ agent-01 should show as connected (no red X)
→ Click agent-01 → Log → Should show "Agent successfully connected"
```

---

### Step 6 — Write the Jenkinsfile

This pipeline explicitly targets your agent using its label.

```groovy
pipeline {
    // Target agent by label — NOT 'agent any' which could run on controller
    agent { label 'linux-agent' }

    stages {
        stage('Verify - Running on Agent') {
            steps {
                // These commands prove WHERE the build is running
                sh 'echo "Hostname: $(hostname)"'
                sh 'echo "Whoami: $(whoami)"'
                sh 'echo "Working dir: $(pwd)"'
                sh 'echo "Build number: ${BUILD_NUMBER}"'
            }
        }

        stage('Verify - Not on Controller') {
            steps {
                // Controller hostname will be different from agent hostname
                sh '''
                    echo "If this hostname matches your Jenkins controller container ID"
                    echo "something is wrong — build is on controller, not agent"
                    hostname
                '''
            }
        }

        stage('Simple Build Task') {
            steps {
                sh 'echo "Build running on agent at: $(date)"'
                sh 'mkdir -p workspace-test && touch workspace-test/build-${BUILD_NUMBER}.txt'
                sh 'ls -la workspace-test/'
            }
        }
    }

    post {
        always {
            echo "Build ${BUILD_NUMBER} completed on agent: ${env.NODE_NAME}"
            cleanWs()
        }
        success {
            echo "SUCCESS — Agent is properly configured"
        }
        failure {
            echo "FAILURE — Check agent connectivity in Manage Jenkins → Nodes"
        }
    }
}
```

**What to verify in the console log:**
```
✅ Running on agent-01        ← first line Jenkins prints, shows which node
✅ hostname = agent container ID (NOT controller container ID)
✅ whoami = jenkins
✅ NODE_NAME = agent-01
✅ No "Running on controller" or "Built-In Node" anywhere in the log
```

---

### Step 7 — Create and Run the Pipeline Job

```
Jenkins UI → New Item
Name:        lab-3.1-static-agent
Type:        Pipeline → OK

Pipeline section:
  Definition:   Pipeline script from SCM
  SCM:          Git
  URL:          your repo URL
  Branch:       */feat/phase-3-agents   ← or your current branch
  Script path:  phase-3-agents/lab-3.1-static-agent/Jenkinsfile

→ Save → Build Now
```

---

### Step 8 — The Break-It Exercise

**Do not skip this.** This is where real learning happens.

```
Exercise 1 — Wrong label
  Change agent label to 'wrong-label' in Jenkinsfile
  Trigger build → What happens? How long does it wait?
  Fix it → Document what the error message looked like

Exercise 2 — Agent offline
  docker stop jenkins-agent-01
  Trigger build → What happens in Jenkins UI?
  docker start jenkins-agent-01 → Does the build recover?
  Document the behaviour

Exercise 3 — Verify it really runs on agent
  Get controller container ID:  docker ps | grep jenkins
  Run a build and look at hostname in console log
  Confirm hostname in log ≠ controller container ID
  Screenshot this as proof
```

---

## ✅ Lab Completion Checklist

```
Setup
[x] jenkins-net Docker network created
[x] SSH key pair generated (jenkins-agent and jenkins-agent.pub)
[x] Agent container running: docker ps shows jenkins-agent-01
[x] Both containers on jenkins-net: docker network inspect jenkins-net

Jenkins Config
[x] SSH private key added to Jenkins credentials (ID: jenkins-agent-ssh-key)
[x] Node agent-01 registered with label: linux-agent
[x] Node shows connected in Manage Jenkins → Nodes (no red X)
[x] Agent log shows: "Agent successfully connected"

Pipeline
[x] Jenkinsfile committed to repo under lab-3.1-static-agent/
[x] Pipeline job created pointing to that Jenkinsfile
[x] Build triggered and passed
[x] Console log proves build ran on agent-01 (not controller)
[x] NODE_NAME = agent-01 visible in build output

Break-It Exercises
[x] Wrong label exercise done — documented what happened
[x] Agent offline exercise done — documented recovery behaviour
[x] Screenshot saved proving hostname differs from controller

Documentation
[x] setup-notes.md filled with every command you ran
[x] README status updated to ✅ Completed
[x] Phase 3 progress tracker updated
[x] Screenshots added to screenshots/ folder
```

---

## 🐛 Troubleshooting Guide

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Agent shows red X in Nodes | SSH connection failed | Check Host is `jenkins-agent-01` not `localhost` |
| "No such host" error | Containers not on same network | Run `docker network connect jenkins-net jenkins` |
| Permission denied (SSH) | Wrong key or username | Username must be `jenkins`, not `root` |
| Build stuck in queue | No agent with matching label | Verify label in Node config matches Jenkinsfile exactly |
| Build runs on controller | `agent any` used instead of label | Change to `agent { label 'linux-agent' }` |
| Port 50000 not reachable | Jenkins container missing port | Recreate container with `-p 50000:50000` |
| Agent connects then drops | Resource issue | Check `docker stats` — agent may be OOM |

---

## 🎤 Interview Talking Points From This Lab

After completing this lab, you can answer:

- **"What is a Jenkins agent and why do you need one?"**
  Controller manages, agents execute. Separating them prevents controller overload and adds build isolation.

- **"How do you connect a static agent to Jenkins?"**
  Via SSH. Controller holds private key as a credential. Agent container runs with the matching public key. Both on same Docker network so they resolve by hostname.

- **"What is an agent label and why does it matter?"**
  Labels let you route specific pipeline stages to specific agents. `agent { label 'linux-agent' }` ensures the build only runs on nodes tagged with that label — not on any random available executor.

- **"How do you prove a build ran on an agent and not the controller?"**
  Check `NODE_NAME` in console log. Check `hostname` output — it will match the agent container ID, not the controller.

---

## 📝 My Learnings — Lab 3.1 Retrospective

> Jenkins detects agent loss automatically
> Build queues silently — does not fail — waits for agent to return
> Agent reconnects automatically once container is back online
> No manual intervention needed in Jenkins UI after restart
> In production this means: static agents do not self-heal Someone or something (systemd, Kubernetes, auto-scaling) must restart the agent — Jenkins only manages the job queue, not the agent infrastructure
> This is exactly why dynamic agents (Lab 3.2) are preferred — no persistent agent means nothing to recover from

### What I Built

### What Broke and How I Fixed It

### What Was Confusing Before I Built It

### Key Command That Saved Me

### What I Would Do Differently

---

## 🔗 References

- [Jenkins SSH Agent Docker Image](https://hub.docker.com/r/jenkins/ssh-agent)
- [Jenkins Distributed Builds Official Docs](https://www.jenkins.io/doc/book/using/using-agents/)
- [Managing Nodes in Jenkins](https://www.jenkins.io/doc/book/managing/nodes/)

---

*Part of [Phase 3 — Agents](../README.md) | [Jenkins DevOps Learning Labs](../../README.md)*
