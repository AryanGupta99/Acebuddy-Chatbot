# Disk Space Full - Storage Upgrade - AceBuddy Knowledge Base

## Issue
Customer's storage is running low or full, causing system slowdown or failures.

## Symptoms
- Receiving "Low Disk Space" warning
- Applications running slowly
- Cannot save new files
- System freezing periodically
- Backup failures
- Database performance degradation

## Automated Solution Overview
The AceBuddy chatbot presents storage upgrade options, captures customer preference, and automatically forwards the request to the Point of Contact (POC) for approval.

## Step-by-Step Solution

### For Users (via Chatbot)
1. User initiates chat: "My disk is running low" or "I need more storage"
2. Chatbot displays available upgrade plans:
   - 200 GB for $120/month
   - 100 GB for $60/month
   - 80 GB for $50/month
   - 60 GB for $40/month
   - 40 GB for $28/month

3. User selects preferred storage plan
4. Chatbot captures:
   - Selected plan (GB and cost)
   - Current disk usage percentage
   - Primary use case (accounting data, files, backups, etc.)
   - Preferred start date

5. Chatbot automatically emails POC/Account Manager with:
   - Customer request
   - Selected plan
   - Business justification
   - Approval link/form

6. User receives confirmation: "Your storage upgrade request has been sent to [POC Name]. Expected approval: 24-48 hours."

### For Support Team / POC
1. Receive automated request from chatbot
2. Review customer selection and current usage
3. Approve or negotiate plan
4. Send approval notification to customer
5. Coordinate with billing/infrastructure team
6. Provision storage
7. Update ticket status

## Storage Recommendations
- Light users (QB only, <50GB/month): 40-60 GB plan
- Standard users (QB + files, 50-100GB/month): 80-100 GB plan
- Heavy users (QB + large backups + archive, >100GB/month): 200 GB plan

## Expected Outcome
- Storage upgrade request processed in 24-48 hours
- Customer self-selects plan (reduces negotiation)
- POC receives pre-filled approval request
- Clear communication and tracking
- Proactive capacity management

## Time Savings
- Before: 20-30 minutes per request (agent collection, email, follow-up)
- After: 3-5 minutes per request (POC review only)
- Annual impact: ~5-8 hours saved per agent per month

## Success Criteria
- Customer receives plan options within 30 seconds
- Storage upgrade processed within 48 hours of approval
- Zero follow-ups needed for clarification
- Billing and provisioning teams receive complete information

## Preventing Disk Full Issues
1. Monitor disk usage monthly
2. Archive old files regularly
3. Delete temporary/backup files not needed
4. Schedule automatic backups to separate storage
5. Request proactive upgrade before reaching 85% capacity

## Related Topics
- Server Performance
- System Maintenance
- Backup Management
- Disk Usage Monitoring

## Troubleshooting
If storage not increasing after upgrade:
1. Verify provisioning completed on server
2. Check if OS needs refresh to recognize new space
3. Verify system is using new storage
4. Escalate to infrastructure team if issue persists
