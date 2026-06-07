# Break-It Exercise 1 - Missing Stash

## Objective

Understand why artifacts do not automatically move between Jenkins agents.

## Change Made

Removed:

```groovy
stash(
    name: 'build-artifact',
    includes: 'build/**'
)
```

from the Linux Agent stage.

## Expected Result

The Docker Agent stage should fail during:

```groovy
unstash 'build-artifact'
```

## Actual Result

Pipeline failed in the Docker Agent stage.

```text
ERROR: No such saved stash ‘build-artifact
```

## Root Cause

The artifact was created on the Linux Agent but never stored in Jenkins using `stash`.

Since the Docker Agent executes in a different workspace, it cannot directly access files created on another agent.

The `unstash` step failed because Jenkins had no saved artifact named `build-artifact`.

## Fix

Restored:

```groovy
stash(
    name: 'build-artifact',
    includes: 'build/**'
)
```

## Key Learning

Jenkins agents have isolated workspaces.

Files created on one agent are not automatically available on another agent.

`stash` and `unstash` are required to transfer artifacts between agents in distributed pipelines.


# Break-It #2 - Invalid Agent Label

### Change

Changed:

```groovy
label 'linux-agent'
```

to:

```groovy
label 'invalid-agent'
```

### Result

Pipeline remained queued and could not start.

### Root Cause

Jenkins could not find any agent matching the requested label.

### Fix

Restored the correct label:

```groovy
label 'linux-agent'
```

### Learning

Agent labels must match available nodes. Incorrect labels prevent Jenkins from scheduling builds.



