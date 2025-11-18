# Server Performance Issues - CPU / RAM / Disk Full - AceBuddy Knowledge Base

## Issue
Server or computer is running slowly, freezing, or showing high resource usage.

## Symptoms
- Computer running slowly or freezing
- High CPU usage
- High RAM (memory) usage
- Low disk space
- Applications taking long time to load
- System becomes unresponsive periodically
- Fan running loudly
- Programs crashing or quitting unexpectedly

## Automated Solution Overview
The AceBuddy chatbot asks users to check their Task Manager for resource usage (CPU, RAM, Disk), then provides targeted solutions based on the readings.

## Step-by-Step Solution

### For Users (via Chatbot)
1. User initiates chat: "My computer is running slowly" or "Computer freezing"
2. Chatbot asks: "Let's diagnose the issue. Open Task Manager and check these metrics:"

**Opening Task Manager:**
- Press **Ctrl + Shift + Esc** (fastest method)
- Or: Right-click taskbar → "Task Manager"
- Or: Press **Ctrl + Alt + Delete** → Click "Task Manager"

---

## Diagnostic Questions and Solutions

### Question 1: CPU Usage
**Chatbot asks**: "What is your CPU usage percentage? (Look at 'Performance' tab, 'CPU')"

**If CPU < 50%**: Normal, not the issue

**If CPU 50-80%**: Moderately high
- Solution:
  1. Look at "Processes" tab
  2. Find processes using high CPU (look at "CPU" column)
  3. If unknown application: Close it
  4. If critical application: Try closing and reopening
  5. Restart computer

**If CPU > 80%**: High (causing slowness)
- Solution:
  1. Go to "Processes" tab
  2. Sort by CPU column (click header)
  3. Close non-critical applications
  4. Close web browsers (Chrome uses significant CPU)
  5. Disable background applications
  6. If issue persists: Restart computer

**If CPU stays high after closing apps:**
- Potential malware or system issue
- Contact IT support
- System may need antivirus scan

---

### Question 2: RAM (Memory) Usage
**Chatbot asks**: "What is your RAM usage percentage? (Look at 'Performance' tab, 'Memory')"

**If RAM < 60%**: Normal, not the issue

**If RAM 60-85%**: Moderately high
- Solution:
  1. Close unused applications
  2. Close web browser tabs (each tab uses memory)
  3. Restart programs using high memory
  4. Restart computer

**If RAM > 85%**: Critical (causing system slowness)
- Solution:
  1. Save all work immediately
  2. Close all non-critical applications
  3. Close web browsers completely
  4. Restart your computer
  5. After restart, your memory will be cleared

**If memory usage high even after restart:**
- Application may have memory leak
- Contact IT support
- May need to reinstall problematic application

---

### Question 3: Disk Space
**Chatbot asks**: "What is your Disk usage percentage? (Look at 'Processes' tab → click any process → 'Performance' → 'Disk' OR check disk space in Windows)"

**If Disk < 85%**: Normal, not the issue

**If Disk 85-95%**: Running low on space
- Solution:
  1. Delete temporary files
  2. Remove old/unused applications
  3. Empty Recycle Bin
  4. Archive old documents
  5. Clear Downloads folder
  6. Request disk upgrade from IT

**If Disk > 95%**: Critical (system will slow down severely)
- Solution:
  1. Immediately stop any new file creation
  2. Move large files to external drive (if available)
  3. Delete unnecessary files aggressively
  4. Delete installer files (.exe, .msi files)
  5. Uninstall unused applications
  6. Contact IT: "I need a disk upgrade urgently"

**Check disk space:**
- Click "This PC" in Windows File Explorer
- Right-click your C: drive
- Click "Properties"
- See "Used space" vs "Free space"

---

## Complete Diagnostic Process

**User Provides All Three Metrics:**

1. **All normal (CPU <50%, RAM <60%, Disk <85%)**
   - System should be running fine
   - Slowness may be caused by:
     - Network latency
     - Software issue (QB, application bug)
     - Background processes
   - Chatbot suggests: "Restart your computer and monitor performance"

2. **One metric high**
   - CPU high: Close applications, restart
   - RAM high: Close applications, restart
   - Disk high: Delete files, request upgrade

3. **Multiple metrics high**
   - Indicates system is overloaded
   - Solution: Restart computer immediately
   - Close unused applications after restart
   - If problem persists: Contact IT support

---

## Recommended Actions by Combination

| CPU | RAM | Disk | Recommended Action |
|-----|-----|------|-------------------|
| Low | Low | Low | Everything normal |
| High | Low | Low | Close CPU-heavy apps, restart |
| Low | High | Low | Close applications, restart |
| Low | Low | High | Delete files, request upgrade |
| High | High | Low | Restart computer |
| High | Low | High | Restart, then delete files |
| Low | High | High | Restart, close apps, delete files |
| High | High | High | Restart immediately, aggressive cleanup needed |

---

## Prevention Tips

**For CPU Issues:**
1. Limit number of applications running
2. Keep Windows updated
3. Run antivirus scans regularly
4. Close web browser when not in use

**For RAM Issues:**
1. Restart computer regularly (weekly)
2. Close unused applications
3. Limit web browser tabs (each = memory)
4. Consider RAM upgrade if frequent issues

**For Disk Issues:**
1. Archive old files regularly
2. Delete temporary files monthly
3. Clean up Downloads folder
4. Request upgrade before reaching 90%

---

## When to Escalate to IT Support

Contact IT if:
- CPU high after closing all applications
- RAM high immediately after restart
- Disk > 95% and no files to delete
- System still slow after troubleshooting
- Performance affecting work productivity
- Error messages appearing
- System crashes or freezes frequently

---

## Expected Outcome
- 60-70% of performance issues resolved by user
- User understands their system resources
- Clear escalation path for complex issues
- IT receives diagnostic data upfront
- Reduced support tickets through prevention

## Time Savings
- Before: 20-30 minutes per ticket (remote diagnosis)
- After: 5-10 minutes per user (self-diagnosis)
- Annual impact: ~5-8 hours saved per support agent

## Success Criteria
- User can diagnose own performance issue
- System performance improved or escalated appropriately
- IT receives complete diagnostic information
- No repeat tickets for same issue

## Related Topics
- System Performance
- Resource Monitoring
- Application Management
- Storage Management
- Computer Maintenance

## Troubleshooting
For persistent performance issues:
1. Document resource metrics when issue occurs
2. Note which applications are running
3. Check for recently installed software
4. Verify no malware present
5. Contact IT with complete diagnostic data
