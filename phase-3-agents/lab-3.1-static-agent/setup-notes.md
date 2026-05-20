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
- break-it-1-build-passed-after-fix.png 

## Break-It Exercise 2 — Agent Offline

### What I Did
- Stopped agent container: docker stop jenkins-agent-ssh-connection

### What Happened in Jenkins UI
- jenkins-agent-ssh-connection showed red X in Manage Jenkins → Nodes
- Build entered queue — did not run
- Queue reason: agent offline / no available executor

### Recovery
- Ran: docker start jenkins-agent-ssh-connection
- Agent reconnected automatically — red X disappeared
- No manual re-registration needed in Jenkins UI
- Queued build resumed and completed successfully
- Console log confirmed: Running on jenkins-agent-ssh-connection

### Key Takeaways
- Jenkins detects agent loss automatically
- Build queues silently — does not fail — waits for agent to return
- Agent reconnects automatically once container is back online
- No manual intervention needed in Jenkins UI after restart
- In production this means: static agents do not self-heal
  Someone or something (systemd, Kubernetes, auto-scaling) must
  restart the agent — Jenkins only manages the job queue, not
  the agent infrastructure
- This is exactly why dynamic agents (Lab 3.2) are preferred —
  no persistent agent means nothing to recover from

### Screenshot Evidence
- break-it-2-agent-red-x.png
- break-it-2-queue-blocked.png
- break-it-2-agent-log-error.png
- break-it-2-agent-fix.png
- break-it-2-build-resumed.png

## Break-It Exercise 3 — Verify Build Runs on Agent

### Container IDs Captured
- Controller: 917dfa1e2026
- Agent:      0d67efb5ac71

### Console Log Evidence
- First line: "Running on jenkins-agent-ssh-connection in /home/jenkins/agent/workspace"
- Hostname output: 0d67efb5ac71  ← matches agent, NOT controller
- NODE_NAME: jenkins-agent-ssh-connection
- whoami: jenkins

### Conclusion
Hostname in console log = agent container ID
Hostname in console log ≠ controller container ID
Build is confirmed running on agent — not controller.

### Key Takeaway
Always verify NODE_NAME and hostname in console log
after setting up a new agent. Never assume agent { label }
is working — prove it with evidence.
Screenshots saved as proof in screenshots/ folder.


