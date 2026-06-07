# 💥 Break-It Exercises - Multi-Agent Pipeline

## Purpose

These exercises demonstrate critical concepts in distributed Jenkins pipelines by intentionally breaking the pipeline and observing the failures.

Each exercise helps understand:
- How Jenkins schedules work across agents
- Why artifact transfer mechanisms are necessary
- Best practices for controller-agent architecture

---

# Break-It Exercise 1 - Missing Stash

## Objective

Understand why artifacts do not automatically move between Jenkins agents and the importance of `stash`/`unstash` for artifact transfer.

## Change Made

Removed the `stash` step from the Linux Agent stage:

```groovy
stash(
    name: 'build-artifact',
    includes: 'build/**'
)
```

## Expected Result

The Docker Agent stage should fail during:

```groovy
unstash 'build-artifact'
```

## Actual Result

Pipeline failed in the Docker Agent stage with error:

```text
ERROR: No such saved stash 'build-artifact'
```

Build status: **FAILURE** ❌

![Missing Stash - Build Failure](screenshots/08-break-it-1-missing-stash-build-failure.png)

![Missing Stash - Error Message](screenshots/09-break-it-1-stash-error-message.png)

## Root Cause

**Workspace Isolation Between Agents**

Each Jenkins agent has its own isolated workspace:

```text
Linux Agent Workspace:
/var/lib/jenkins/workspace/job-name/
    └── build/
        └── app.txt  ← Created here

Docker Agent Workspace:
/tmp/workspace/job-name/
    └── (empty)  ← Cannot see Linux Agent files
```

The artifact (`build/app.txt`) was created on the Linux Agent but never stored in Jenkins using `stash`.

When the Docker Agent tried to `unstash 'build-artifact'`, Jenkins had no saved artifact to retrieve.

**Why This Happens:**
- Different agents = Different machines/containers
- Different filesystems
- No shared storage by default
- Workspaces are completely isolated

## Fix

Restored the stash step:

```groovy
stash(
    name: 'build-artifact',
    includes: 'build/**'
)
```

This stores the artifact in Jenkins internal storage, making it available to any agent via `unstash`.

## Key Learning

**Critical Concept: Workspace Isolation**

Jenkins agents have isolated workspaces. Files created on one agent are NOT automatically available on another agent.

**Artifact Transfer Mechanism:**

```groovy
// Agent 1: Save artifact
stash name: 'my-artifact', includes: 'build/**'

// Agent 2: Retrieve artifact  
unstash 'my-artifact'
```

**Real-World Analogy:**

Think of Jenkins agents like different computers in different locations:
- Computer A creates a file → It's only on Computer A
- Computer B needs that file → Must transfer it explicitly
- `stash`/`unstash` = Jenkins' built-in file transfer system

---

# Break-It Exercise 2 - Invalid Agent Label

## Objective

Understand what happens when Jenkins cannot find a matching agent for the requested label.

## Change Made

Changed:

```groovy
agent {
    label 'linux-agent'
}
```

to:

```groovy
agent {
    label 'invalid-agent'
}
```

## Expected Result

Jenkins should not be able to schedule the pipeline stage because no agent matches the label `invalid-agent`.

## Actual Result

Pipeline remained stuck in the queue indefinitely.

Jenkins console showed:

```text
Waiting for next available executor on 'invalid-agent'
```

The stage never executed because Jenkins could not find a node with the matching label.

![Invalid Agent Label - Build Queued](screenshots/10-break-it-2-invalid-agent-label-queued.png)

## Root Cause

Jenkins agent scheduling depends on matching node labels.

When a pipeline requests a label that doesn't exist on any available agent, Jenkins keeps waiting for a matching executor.

The build remains queued until:
- A matching agent becomes available, OR
- The pipeline times out, OR
- The build is manually aborted

## Fix

Restored the correct label:

```groovy
agent {
    label 'linux-agent'
}
```

![Fixed with Correct Label](screenshots/11-break-it-2-fixed-correct-label-success.png)

## Key Learning

Agent labels are critical for pipeline execution.

Always ensure:
- Labels in the pipeline match available node labels
- Agent nodes are online and available
- Labels are spelled correctly (case-sensitive)

Incorrect labels result in indefinite queuing and pipeline starvation.

---

# Break-It Exercise 3 - Using `agent any` Instead of `agent none`

## Objective

Understand why `agent none` is a best practice for multi-agent pipelines and what happens when using `agent any` at the pipeline level.

## Change Made

Changed:

```groovy
pipeline {
    agent none
    ...
}
```

to:

```groovy
pipeline {
    agent any
    ...
}
```

## Expected Result

The pipeline should allocate a global workspace on the first available agent (potentially the Jenkins Controller or any other agent), which can lead to:
- Unnecessary resource usage
- Workspace pollution
- Controller executing workload (security/scalability risk)

## Actual Result

Pipeline executed successfully, BUT:

- Jenkins allocated a workspace on an agent even though individual stages already specify their own agents
- The global agent remained allocated throughout the entire pipeline execution
- If the Controller was chosen, it violated the best practice of keeping the Controller execution-free

![Agent Any - Controller/Agent Execution](screenshots/12-break-it-3-agent-any-controller-execution.png)

## Root Cause

Using `agent any` tells Jenkins:

> "Allocate me a workspace on any available agent for the entire pipeline"

This causes:
- Double workspace allocation (global + stage-level)
- Wasted executor resources
- Potential Controller execution (bad practice)
- Reduced scalability

## Fix

Restored:

```groovy
pipeline {
    agent none
    ...
}
```

With `agent none`:
- No global workspace is allocated
- Each stage runs only on its explicitly defined agent
- Controller stays free for orchestration
- Better resource utilization

## Key Learning

**Best Practice for Multi-Agent Pipelines:**

```groovy
pipeline {
    agent none  // ← Controller orchestrates only
    
    stages {
        stage('Build') {
            agent { label 'linux-agent' }  // ← Explicit execution
            ...
        }
        
        stage('Test') {
            agent { docker 'python:3.11' }  // ← Explicit execution
            ...
        }
    }
}
```

**Why `agent none` Matters:**

✅ Prevents accidental Controller execution  
✅ Forces explicit agent assignment per stage  
✅ Improves scalability  
✅ Better resource management  
✅ Production-grade architecture  

**Real-World Impact:**

In enterprise Jenkins environments:
- Controllers manage hundreds of pipelines
- Controller CPU/memory must be protected
- Execution should always happen on agents
- `agent none` enforces this separation

---

# 🎯 Summary - What These Exercises Teach

| Exercise | Concept | Real-World Impact |
|----------|---------|-------------------|
| **Break-It 1** | Workspace isolation + artifact transfer | Understanding how files move between agents in distributed systems |
| **Break-It 2** | Agent label matching + scheduling | Preventing pipeline starvation and execution failures |
| **Break-It 3** | Controller vs Agent execution | Enterprise-grade architecture and scalability |

---

# 📚 Key Takeaways for Interviews

**Q: Why can't agents share files directly?**  
A: Each agent has an isolated workspace. They're separate machines/containers with separate filesystems. Jenkins provides `stash`/`unstash` for artifact transfer.

**Q: What happens if an agent label doesn't match?**  
A: The pipeline stage remains queued indefinitely until a matching agent becomes available or the build times out.

**Q: Why use `agent none` at the pipeline level?**  
A: To prevent the Jenkins Controller from executing build workloads. The Controller should orchestrate, not execute. This is critical for scalability and security.

**Q: When would you use multiple agents in a single pipeline?**  
A: When different stages require different environments (Linux vs Windows, different tool versions, ephemeral containers for testing, specialized hardware, etc.).

---

