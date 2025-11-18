# Zobot Data Extraction Summary

**Extraction Date:** 2025-11-11 22:35:36
**Source File:** Acebuddy

## Statistics

- **Total Conversation Nodes:** 166
- **Total Q&A Pairs Extracted:** 187
- **Topics Identified:** 17

## Topics Breakdown

- **General Support:** 89 Q&A pairs
- **Application Management:** 18 Q&A pairs
- **Sage:** 13 Q&A pairs
- **QuickBooks:** 10 Q&A pairs
- **Office 365:** 9 Q&A pairs
- **Support Escalation:** 9 Q&A pairs
- **ProSeries:** 6 Q&A pairs
- **Drake Tax:** 6 Q&A pairs
- **Printer Setup:** 5 Q&A pairs
- **User Management:** 4 Q&A pairs
- **Memory/RAM:** 4 Q&A pairs
- **Lacerte:** 3 Q&A pairs
- **Disk Space:** 3 Q&A pairs
- **Password Reset:** 3 Q&A pairs
- **Server Access:** 2 Q&A pairs
- **ATX:** 2 Q&A pairs
- **Server Management:** 1 Q&A pairs

## Sample Questions by Topic

### General Support

- How do I 134?
- How do I app replacement4?
- How do I ts nlicense1?

### Application Management

- QuickBooks
- ProSeries
- Drake

### Sage

- Looks like you've selected an invalid option, Please try again!
- How do I sage1?
- How do I send message  158?

### QuickBooks

- How do I qbupgrade2?
- QuickBooks is Frozen
- QuickBooks Login Issue

### Office 365

- How do I okoffice3?
- How do I office2?
- How do I office4?

### Support Escalation

- How do I forward  132?
- How do I forward to operator  169?
- How do I busy response  140?

### ProSeries

- How do I proseriesupg3?
- How do I proseriesupg2?
- How do I proseries3?

### Drake Tax

- How do I drakeupg3?
- How do I drake3?
- How do I drakeupg2?

### Printer Setup

- How do I uniprint1?
- Printer Addition
- Scanner Addition

### User Management

- User Addition
- User Removal
- User Replacement

### Memory/RAM

- How do I ramadd3?
- How do I ramadd2?
- How do I ramadd4?

### Lacerte

- How do I lacerte1?
- How do I lacerte3?
- How do I lacerte2?

### Disk Space

- How do I diskspace3?
- How do I diskspaceaddition?
- How do I diskspace2?

### Password Reset

- Already Enrolled to Selfcare Portal
- Not Enrolled to Selfcare Portal
- Please select an option below

### Server Access

- How do I mac rdp?
- How do I rdp - windows?

### ATX

- How do I atx2?
- How do I atx1?

### Server Management

- How do I server reboot1?


## Output Files Generated

1. **JSON Database:** `zobot_qa_pairs.json` - 187 Q&A pairs
2. **Topic Documents:** `topics/` folder - 17 markdown files
3. **Master Document:** `acebuddy_chatbot_knowledge.md` - Complete knowledge base
4. **This Report:** `extraction_summary.md`

## Next Steps

1. Review the extracted documents in the `topics/` folder
2. Check the master document for completeness
3. Run the RAG ingestion script to add this data to ChromaDB:
   ```bash
   python scripts/ingest_zobot_to_rag.py
   ```
