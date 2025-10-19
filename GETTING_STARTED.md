# Getting Started with Hybrid IDS

**Final Year B.Tech Project Guide**
**Author:** Syed Misbah Uddin | Central University of Jammu

---

## Welcome! 🎓

This guide will help you understand and deploy my **two-tier intrusion detection system** developed as a final year B.Tech project in Cybersecurity.

Get the system up and running in 3 simple steps.

---

## Step 1: Understand What This Is (5 minutes)

### Read This First
👉 **[ARCHITECTURE_EXPLAINED.md](ARCHITECTURE_EXPLAINED.md)**

**Key concept to understand:**

```
Traffic → Tier 1 (S-IDS) → Known threat? → Alert
                ↓
              Unknown
                ↓
          Tier 2 (A-IDS) → ML Analysis → Threat? → Alert + Review
                ↓                              ↓
              Safe                      Human validates
                                              ↓
                                        New signature
                                              ↓
                                        Updates Tier 1
                                              ↓
                                     System gets smarter!
```

**Why this is cool:**
- Fast detection of known threats (Tier 1)
- Smart detection of unknown threats (Tier 2)
- System learns from experience (Feedback loop)

---

## Step 2: Deploy the System (30-45 minutes)

### Read This Second
👉 **[COMPLETE_INTEGRATION_GUIDE.md](COMPLETE_INTEGRATION_GUIDE.md)**

**Quick Version:**

**A. Install Dependencies**
```bash
# Windows (MSYS2)
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake

# Linux
sudo apt install build-essential cmake libpcap-dev

# Both
pip install -r requirements.txt
```

**B. Build C++ Components**
```bash
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j4
```

**C. Start ELK Dashboard**
```bash
cd ../elk
docker-compose up -d
```

**D. Run Detection Engines (4 terminals)**
```bash
# Terminal 1: S-IDS (Tier 1)
./build/sids -i eth0

# Terminal 2: A-IDS Feature Extraction
./build/nids -i eth0 --extract-features

# Terminal 3: A-IDS ML Engine
python src/ai/inference/zmq_subscriber.py --model-dir models/

# Terminal 4: HIDS
python src/hids/hids_main.py
```

**E. Access Dashboard**
```
http://localhost:5601
```

---

## Step 3: Test & Validate (15-30 minutes)

### Read This Third
👉 **[VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)**

**Quick Tests:**

**1. Test S-IDS (Tier 1)**
```bash
./build/sids -r test.pcap
# Should detect known patterns
```

**2. Test A-IDS (Tier 2)**
```bash
./build/nids -r test.pcap --extract-features
# Should create features.csv
```

**3. Test HIDS**
```bash
cd src/hids
python file_monitor.py --create-baseline
echo "test" >> /path/to/monitored/file
python file_monitor.py --check
# Should detect file modification
```

**4. View in Dashboard**
- Open http://localhost:5601
- Import dashboard: `elk/kibana/dashboards/unified-security-dashboard.ndjson`
- Check for alerts from all three systems

---

## For Your Report

### What to Include

**1. Architecture Explanation**
- Draw the two-tier pipeline diagram
- Explain why it's better than single-layer
- Describe the feedback loop

**2. Implementation**
- Show components you deployed
- Screenshots of running systems
- Dashboard visualizations

**3. Testing Results**
- What attacks did you test?
- Which tier detected what?
- Any false positives?
- Performance metrics

**4. Analysis**
- Compare S-IDS vs A-IDS effectiveness
- Discuss trade-offs (speed vs accuracy)
- Suggest improvements

---

## Common Issues

**"Permission denied" when capturing packets**
```bash
# Linux: Add capabilities
sudo setcap cap_net_raw,cap_net_admin=eip ./build/nids

# Or use PCAP files instead
./build/nids -r test.pcap
```

**"Elasticsearch won't start" (memory error)**
```bash
# Reduce memory in elk/docker-compose.yml
ES_JAVA_OPTS=-Xms2g -Xmx2g  # Instead of 4g
```

**"No alerts in dashboard"**
```bash
# Check logs exist
ls -lh *.log

# Check Logstash is running
docker-compose logs logstash

# Verify file paths in docker-compose.yml
```

---

## Documentation Roadmap

```
Start Here:
1. [README.md](README.md)
   └─> Quick overview and quick start

Deep Dive:
2. [ARCHITECTURE_EXPLAINED.md](ARCHITECTURE_EXPLAINED.md)
   └─> Understand two-tier pipeline

Deploy:
3. [COMPLETE_INTEGRATION_GUIDE.md](COMPLETE_INTEGRATION_GUIDE.md)
   └─> Full deployment guide

Test:
4. [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)
   └─> Testing procedures

Understand Structure:
5. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
   └─> Code organization

Optional/Reference:
6. [ELK_DASHBOARD_GUIDE.md](ELK_DASHBOARD_GUIDE.md)
7. [REAL_TIME_DEPLOYMENT.md](REAL_TIME_DEPLOYMENT.md)
8. [BUGFIX_AI_ENGINE.md](BUGFIX_AI_ENGINE.md)
9. [ORIGINAL_PLAN.md](ORIGINAL_PLAN.md)
```

---

## Quick Command Reference

| What You Want | Command |
|---------------|---------|
| Build system | `cd build && cmake .. && make` |
| Run S-IDS | `./build/sids -i eth0` |
| Run A-IDS | `./build/nids -i eth0 --extract-features` |
| Run HIDS | `python src/hids/hids_main.py` |
| Start dashboard | `cd elk && docker-compose up -d` |
| View dashboard | `http://localhost:5601` |
| Stop everything | `docker-compose down && Ctrl+C` |

---

## Success Checklist

Minimum viable project:
- [ ] Built C++ components
- [ ] ELK Stack running
- [ ] At least one detection tier working
- [ ] Some alerts in dashboard
- [ ] Screenshots captured
- [ ] Understand the architecture

Advanced/higher grade:
- [ ] All three systems running (S-IDS, A-IDS, HIDS)
- [ ] Tested multiple attack types
- [ ] Performance comparison documented
- [ ] Feedback loop demonstrated
- [ ] Limitations discussed

---

## Need Help?

**Documentation:**
- Everything is explained in the markdown files above
- Start with ARCHITECTURE_EXPLAINED.md

**Code Issues:**
- Check BUGFIX_AI_ENGINE.md for known issues
- Check VALIDATION_CHECKLIST.md for troubleshooting

**GitHub:**
- Issues: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues
- Discussions: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/discussions

---

## The Big Picture

**What you're building:** An intelligent IDS that combines the speed of signature detection with the intelligence of machine learning, and gets smarter over time through human feedback.

**Why it matters:** Real security operations centers use similar multi-tier approaches. You're learning real-world concepts in a hands-on way.

**Your contribution:** Understanding and demonstrating these concepts shows you grasp advanced cybersecurity principles.

Good luck with your project! 🚀

---

**Last Updated:** 2025-10-19
**Type:** Quick start guide
**Estimated Time:** 1-2 hours for basic deployment

---

**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity
**Project Type:** Final Year B.Tech Major Project
**Last Updated:** October 2025
**Estimated Time:** 1-2 hours for basic deployment
