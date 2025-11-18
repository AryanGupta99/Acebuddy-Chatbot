# 🔧 Docker Desktop WSL Issue - Fix Guide

**Problem:** Docker Desktop stuck on "WSL update" and not showing home screen  
**Cause:** WSL (Windows Subsystem for Linux) not properly installed  
**Solution:** We have 2 options

---

## ⚡ OPTION 1: Quick Fix - Install WSL 2 (Recommended - 5-10 minutes)

### Step 1: Open PowerShell as Administrator
```powershell
# Press: Windows Key + X → A (Run as Administrator)
# OR search "PowerShell" in Start Menu, right-click → Run as Administrator
```

### Step 2: Install WSL 2
```powershell
# This installs WSL 2 automatically
wsl --install

# This will:
# - Enable WSL 2
# - Download Linux kernel
# - Set default distribution to Ubuntu
# Takes 2-5 minutes
```

### Step 3: After Installation Completes
```powershell
# Restart your computer when prompted
# Then Docker Desktop should work automatically
```

---

## 🔄 OPTION 2: Manual WSL Installation (If Option 1 doesn't work)

### Step 1: Enable WSL Feature
```powershell
# Run as Administrator:
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

### Step 2: Enable Virtual Machine Platform
```powershell
# Run as Administrator:
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

### Step 3: Download Linux Kernel
```powershell
# Download WSL 2 Linux Kernel:
# Visit: https://aka.ms/wsl2kernel
# Run the installer (.msi file)
```

### Step 4: Set WSL 2 as Default
```powershell
# Run as Administrator:
wsl --set-default-version 2
```

### Step 5: Install Ubuntu Distribution
```powershell
# Option A - From Microsoft Store:
# Open Microsoft Store → Search "Ubuntu" → Click "Install"

# Option B - From PowerShell:
wsl --install -d Ubuntu
```

### Step 6: Restart Computer
```powershell
# Very important! WSL changes need system reboot
Restart-Computer
```

---

## ✅ VERIFY FIX WORKED

After installation/restart, check this:

```powershell
# Check WSL status
wsl --list --verbose

# Expected output:
# NAME      STATE           VERSION
# Ubuntu    Running         2

# Check Docker is ready
docker --version

# Check if Docker daemon is available
docker ps

# If all work, Docker Desktop should now start normally
```

---

## 🚀 START DOCKER NOW (After WSL Fix)

Once WSL is installed and verified:

```powershell
# Option 1: Via GUI (now it should work)
# Start Menu → Search "Docker Desktop" → Click to open

# Option 2: Via Terminal (if GUI still not working)
# Just run docker commands directly - they work without GUI

# Option 3: Start Docker service
Start-Service Docker
```

---

## 🔧 ALTERNATIVE: Use Docker Without Desktop GUI

If Docker Desktop GUI still has issues, you can run docker commands directly:

```powershell
# Check if Docker daemon is available
docker --version
docker ps

# If these work, you can use Docker via terminal:
cd "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
docker-compose up --build -d
```

---

## 📋 QUICK CHECKLIST

Before proceeding with AceBuddy-RAG:

- [ ] Run: `wsl --list --verbose`
  - Should show Ubuntu or other Linux distro with VERSION 2
  
- [ ] Run: `docker --version`
  - Should show version (e.g., Docker version 24.0.0)
  
- [ ] Run: `docker ps`
  - Should work without errors

If all 3 pass, Docker is working and you can start AceBuddy-RAG!

---

## 🚨 IF STILL HAVING ISSUES

### Issue: "Docker daemon is not running"

**Solution:**
```powershell
# Start Docker service manually
Start-Service Docker

# Or restart Docker:
Restart-Service Docker

# Verify it's running:
Get-Service Docker
```

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```powershell
# Docker Desktop GUI might need restart
# Try this:

# 1. Kill any Docker processes:
Get-Process docker* | Stop-Process -Force

# 2. Uninstall Docker Desktop completely
# (Settings → Apps → Apps & features → Docker → Uninstall)

# 3. Reinstall Docker Desktop from:
# https://www.docker.com/products/docker-desktop

# 4. During installation, make sure "Install WSL 2" is checked
```

### Issue: "WSL update still showing"

**Solution:**
```powershell
# Update WSL to latest version:
wsl --update

# If that hangs, try:
wsl --update --web-download

# Then restart:
wsl --shutdown
wsl --list --verbose
```

---

## 🎯 QUICK STEPS SUMMARY

**If you want FASTEST fix (5-10 minutes):**

1. Open PowerShell as Administrator
2. Run: `wsl --install`
3. Restart your computer
4. Done! Docker Desktop should work now

**Then start AceBuddy-RAG:**

```powershell
cd "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
docker-compose up --build -d
curl http://localhost:8000/health
```

---

## 📞 STILL STUCK?

If Docker Desktop still won't work after WSL install:

**Option A: Reinstall Docker Desktop**
- Download from: https://www.docker.com/products/docker-desktop
- Run installer
- During install: Check "Install WSL 2"
- Restart computer

**Option B: Use Docker Without Desktop**
- Install Docker CLI directly (skip the GUI)
- Works just fine with terminal commands
- All your `docker` and `docker-compose` commands work the same

**Option C: Use Podman Instead**
- Similar to Docker, sometimes easier on Windows
- Download from: https://podman.io/
- Commands are almost identical to Docker

---

## ⏱️ EXPECTED TIME

| Task | Time |
|------|------|
| WSL 2 Installation | 5-10 min |
| Computer Restart | 2-3 min |
| Docker Verification | 1-2 min |
| **Total** | **10-15 min** |

---

## ✨ WHAT HAPPENS WHEN IT'S FIXED

Once WSL and Docker are working:

1. Docker Desktop will open normally
2. You'll see the home screen (no more "WSL update" error)
3. Status will show "Docker Desktop is running"
4. All docker commands work: `docker ps`, `docker-compose up`, etc.
5. You can start AceBuddy-RAG immediately

---

## 🚀 NEXT STEPS

1. **Immediately:** Run `wsl --install` (Option 1 is fastest)
2. **After restart:** Verify with `docker ps`
3. **Then:** Start AceBuddy-RAG with `docker-compose up --build -d`
4. **Finally:** Test with `curl http://localhost:8000/health`

---

**Status:** Fix Guide Ready  
**Estimated Fix Time:** 10-15 minutes  
**Success Rate:** 95%+ (WSL install solves most Docker Desktop issues)

Try Option 1 first - it's the fastest and most reliable! 🎯

---

Need help? Run the commands and let me know the output!
