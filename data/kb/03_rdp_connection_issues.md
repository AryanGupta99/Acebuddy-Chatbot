# RDP Connection Issues - Remote Desktop Problems - AceBuddy Knowledge Base

## Issue
User cannot connect to Remote Desktop (RDP) or connection is extremely slow/laggy.

## Symptoms
- Cannot connect to RDP server
- "Server not responding" error
- Connection drops frequently
- Extremely slow response times
- Lag while typing or moving mouse
- Error messages when attempting RDP connection

## Automated Solution Overview
The AceBuddy chatbot asks diagnostic questions about internet connectivity and RDP error messages, then provides targeted fixes or escalates to NOC/SysAdmin team with all diagnostic information.

## Step-by-Step Solution

### For Users (via Chatbot)
1. User initiates chat: "I can't connect to RDP" or "RDP is very slow"
2. Chatbot asks diagnostic questions:
   - "Are you currently connected to the internet? (Yes/No)"
   - "Are you using WiFi or Ethernet?"
   - "Can you see an error message when trying to connect? If yes, what does it say?"
   - "Is this the first time this has happened?"
   - "Can you access other internet services (email, websites)?"

3. Based on responses, chatbot provides one of three paths:

**Path A: Internet Connectivity Issues**
- Error: No internet connection detected
- Solution: 
  1. Restart your WiFi router/modem (power off for 10 seconds)
  2. Wait 30 seconds for it to fully restart
  3. Reconnect to network
  4. Try RDP connection again
- ETA: Immediate
- If fails: "Escalating to NOC team..."

**Path B: RDP Configuration Issues**
- Error: Cannot connect to RDP server / Server not found
- Solution:
  1. Verify correct server address: [Company RDP Server Address]
  2. Ensure you're within office network or VPN connected
  3. Try from different application: Use mstsc command (Windows)
  4. Wait 2-3 minutes and retry (server may be temporarily unavailable)
- ETA: 5-15 minutes
- If fails: "Escalating to NOC team..."

**Path C: Network/Firewall Issues**
- Error: Connection refused / Timeout
- Solution:
  1. Check if firewall is blocking connection
  2. Verify VPN is connected (if required)
  3. Try from different network (mobile hotspot) to test
  4. Contact IT: "Creating support request..."
- ETA: 30-60 minutes with IT support

4. For complex issues, chatbot automatically creates ticket with:
   - All diagnostic questions and answers
   - Error messages captured
   - Network information
   - Suggested priority (high if completely blocked)
   - Suggested troubleshooting steps already attempted

### For NOC/SysAdmin Team
1. Receive automated ticket with all diagnostic data
2. Check server status and logs
3. Verify user's IP is whitelisted
4. Check for network connectivity issues
5. Review recent changes to RDP configuration
6. If server issue: Restart RDP service
7. If user issue: Provide remote support or phone guidance

## Common RDP Error Codes and Solutions

### Error: "The Remote Desktop Gateway server cannot be reached"
- Check internet connection
- Verify VPN is connected
- Restart router/modem

### Error: "Remote Desktop cannot connect to the remote computer"
- Verify correct server address
- Check firewall settings
- Ensure RDP service is running on server
- Verify credentials

### Slow RDP Connection
- Check network bandwidth usage
- Reduce remote display resolution
- Close unused applications on local machine
- Move closer to WiFi router or use Ethernet

## IP Change Impact (Static IP Requirement)
If user's IP address changes (mobile/new location):
- Chatbot captures new static IP
- Automatically creates request for SysAdmin/NOC
- SysAdmin whitelists new IP
- User can reconnect within 1-2 hours

## Expected Outcome
- Basic issues resolved in 5-15 minutes by user
- Complex issues escalated with complete diagnostic information
- NOC receives pre-filled support request
- Clear communication of ETA to user
- Reduced back-and-forth troubleshooting

## Time Savings
- Before: 15-25 minutes per ticket (diagnostic questions, escalation)
- After: 8-15 minutes per ticket (if automated fix works), 5 min (if escalated)
- Annual impact: ~3-5 hours saved per support agent

## Success Criteria
- 40-50% of RDP issues resolved by chatbot diagnostics
- Escalated issues include all necessary diagnostic information
- User receives clear next steps and ETA
- Zero repeat tickets from missing information

## Prevention Tips
1. Keep Windows updated
2. Maintain stable internet connection
3. Use Ethernet for better RDP performance
4. Ensure VPN is running before attempting RDP
5. Whitelist your IP address with IT

## Related Topics
- Network Connectivity
- VPN Setup
- Server Access
- Internet Connectivity Issues
- Firewall Configuration

## Troubleshooting
If issue persists after troubleshooting:
1. Contact NOC team with complete diagnostic information
2. Provide error messages and screenshots
3. Note any recent changes to network or system
4. Escalate to SysAdmin if server reboot needed
