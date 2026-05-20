## Break-It Exercise 1 — Wrong Agent Label

### What I Changed
- Jenkinsfile agent label changed from 'linux-agent' to 'wrong-label'

### What Happened
- Build did NOT fail immediately
- Build entered the queue and waited
- Jenkins UI showed: "There are no nodes with the label 'wrong-label'"
- Build queue (left sidebar on Dashboard) showed the stuck build
- Waited approximately X minutes before I cancelled manually

### Key Learning
- Jenkins does not throw an immediate error for wrong labels
- It assumes an agent with that label might come online later
- In production this means a misconfigured label silently blocks
  your entire pipeline — no alert, no failure email, just silence
- Always verify agent labels match exactly — case sensitive

### Fix Applied
- Restored label to 'linux-agent' in Jenkinsfile
- Build ran successfully on agent-01 immediately after fix

### Screenshot Evidence
- break-it-1-queue-stuck.png
- break-it-1-no-node-error.png
