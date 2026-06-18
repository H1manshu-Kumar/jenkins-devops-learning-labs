# 🧪 Lab 07 - Backup & Restore Jenkins

> Learn how to back up and restore Jenkins to simulate disaster recovery scenarios.

---

## 🎯 Objective

In this lab, we will:

- Understand Jenkins Home structure
- Perform Jenkins backup
- Simulate controller failure
- Restore Jenkins from backup
- Validate recovery

This mirrors real production incidents where CI systems must be restored quickly.

---

## 🧠 Why This Lab Matters

In production:

- Controllers may crash
- Disk corruption may occur
- Accidental deletion can happen
- Disaster recovery is critical

Without backup, CI pipelines and history are permanently lost.

---

## 🏗️ What Needs Backup

Jenkins stores data in:

/var/jenkins_home

This includes:

- Jobs
- Build history
- Credentials
- Plugins
- Configuration
- Workspace metadata

---

## 🧰 Prerequisites

- Lab 01 to 06 completed
- Jenkins running in Docker
- Some pipelines already created

---

## 🚀 Step 1 - Verify Jenkins Home Volume

Check running container:

```bash
docker inspect jenkins
```

Confirm volume mapping:

jenkins_home → /var/jenkins_home   

<img width="477" height="218" alt="image" src="https://github.com/user-attachments/assets/df4d9690-6e2e-4413-8a0d-0770b6ad57f4" />

---

## 💾 Step 2 - Take Backup

Run:

```bash
docker cp jenkins:/var/jenkins_home ./jenkins_backup
```

Verify backup folder exists locally.   

<img width="1191" height="48" alt="image" src="https://github.com/user-attachments/assets/90dbc031-ab08-4339-a13d-c85a06e49e43" />
</br>
<img width="1171" height="292" alt="image" src="https://github.com/user-attachments/assets/bd08e968-24b6-4ff7-ab5c-d7c7755a4d1a" />

---

## 🔥 Step 3 - Simulate Failure

Stop Jenkins:

```bash
docker stop jenkins
```
<img width="287" height="45" alt="image" src="https://github.com/user-attachments/assets/72fe32b6-8b74-4c08-aada-9e2e953ad524" />

Remove container:

```bash
docker rm jenkins
```
<img width="254" height="44" alt="image" src="https://github.com/user-attachments/assets/596890f9-eee4-42f1-9ff1-38293544e714" />

---

## ♻️ Step 4 - Restore Jenkins

Create new container:

```bash
docker run -d   --name jenkins-controller   -p 8080:8080   -p 50000:50000   -v $(pwd)/jenkins_backup:/var/jenkins_home   jenkins/jenkins:lts
```
<img width="654" height="78" alt="image" src="https://github.com/user-attachments/assets/331a5f08-5acf-40a1-ae09-d75b34417a0d" />

---

## 👀 Step 5 - Validate Restoration

Open:

http://localhost:8181

Verify:

- Jobs restored
- Build history present
- Credentials intact
- Plugins available
  
<img width="1280" height="546" alt="image" src="https://github.com/user-attachments/assets/1ac622ec-bf92-43da-9940-7f2fffc65b5e" />

---

## 📊 Expected Behavior

- Jenkins loads previous configuration
- All jobs visible
- No data loss

---

## 🧠 Deep Learning Notes

- Jenkins durability depends entirely on:
- Jenkins Home persistence.
- If Jenkins Home is lost:
- Everything is lost and cannot br restored

---

## 🛠️ Failure Simulation

- Corrupt a job config file.
- Restart Jenkins.
- Observe failure in job loading.

---

## 🧑‍💻 Real Production Insights

Best practices:

- Regular automated backups
- Store backups offsite
- Monitor disk usage
- Test restoration periodically

---

## 🎓 Interview Talking Points

Be ready to explain:

- What should be backed up in Jenkins?
- How do you restore Jenkins?
- What happens if Jenkins Home is lost?
- How to design disaster recovery?

**Strong answer:** “Jenkins durability depends on Jenkins Home persistence; regular backups are essential.”

---
## 📌 Lessons Learned

* Jenkins stores all critical data inside Jenkins Home.
* Jobs, build history, credentials, and plugins depend on Jenkins Home.
* Losing Jenkins Home results in complete CI data loss.
* Backups must include configuration and plugin data.
* Restoration validates backup integrity.
* Container removal does not matter if volume is preserved.
* Disaster recovery planning is essential for CI reliability.
* Backup without restore testing is incomplete.
* Persistent storage design determines Jenkins durability.
* CI systems require regular automated backups.

---

## 🏁 Lab Completion Checklist

- [x] Backup taken
- [x] Failure simulated
- [x] Jenkins restored
- [x] Jobs verified

---

> Backup strategy defines CI reliability in production.
---
## ✍️ Author

**[Himanshu Kumar](https://www.linkedin.com/in/h1manshu-kumar/)** - Learning by building, documenting, and sharing 🚀
