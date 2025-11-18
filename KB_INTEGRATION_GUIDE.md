# KB ARTICLE INTEGRATION GUIDE

**Objective:** Download ~200 KB articles from SharePoint, process them, create atomic chunks, and integrate with existing AceBuddy chatbot system.

---

## 🎯 Complete Pipeline Overview

```
1. Download Excel file from SharePoint
   ↓
2. Parse Excel to extract KB article links
   ↓
3. Batch download all KB articles (PDF, DOCX, etc.)
   ↓
4. Clean & preprocess text (extract, deduplicate, normalize)
   ↓
5. Create atomic chunks (150-200 tokens each)
   ↓
6. Embed with OpenAI (text-embedding-3-small)
   ↓
7. Ingest into Chroma (merge with existing 92 chunks)
   ↓
8. Run smoke tests to verify quality improvement
```

---

## 📋 Step-by-Step Instructions

### **Step 1: Manual Download of Excel File**

Because SharePoint link is protected (403 Forbidden), you must download manually:

1. Open link in browser: https://cloudspacetechnologies-my.sharepoint.com/:x:/r/personal/sumant_choudhary_myrealdata_in/Documents/SOP%20update%20sheet.xlsx
2. Click "Download"
3. Save file to: `data/SOP_update_sheet.xlsx`

```bash
# Verify file exists
ls -la data/SOP_update_sheet.xlsx
```

---

### **Step 2: Parse Excel & Extract KB Links**

Run the link extraction script:

```bash
python scripts/process_kb_articles.py
```

**What it does:**
- ✅ Parses Excel file
- ✅ Extracts all URLs (KB articles, SOPs, etc.)
- ✅ Saves links to: `data/kb_article_links.json`
- ✅ Starts batch download (limited to 10 for testing)

**Output files:**
- `data/kb_article_links.json` - All extracted links
- `data/kb_downloads/download_results.json` - Download status
- `data/kb_downloads/downloaded/` - Downloaded files

---

### **Step 3: Download All KB Articles**

To download ALL articles (instead of just 10):

Edit `scripts/process_kb_articles.py` line ~260:
```python
# Change this:
results = processor.download_articles(links, max_articles=10)

# To this:
results = processor.download_articles(links)  # Remove max_articles
```

Then run again:
```bash
python scripts/process_kb_articles.py
```

**Expected:**
- 200+ KB articles downloaded
- PDFs, DOCX, HTML, etc. extracted
- `data/kb_downloads/downloaded/` contains all files

---

### **Step 4: Clean & Preprocess Downloaded Files**

```bash
python scripts/process_kb_articles.py
```

The same script continues after download to:
- ✅ Extract text from PDFs/DOCX
- ✅ Remove duplicates & noise
- ✅ Normalize formatting
- ✅ Save clean text to: `data/kb_downloads/cleaned/`

**Output:**
- `data/kb_downloads/cleaned/*.txt` - Cleaned articles
- `data/kb_downloads/cleaning_results.json` - Statistics

---

### **Step 5: Create Atomic Chunks**

```bash
python scripts/chunk_kb_articles.py
```

**What it does:**
- ✅ Reads cleaned articles
- ✅ Splits into atomic 150-200 token chunks
- ✅ Preserves title and source metadata
- ✅ Saves to: `data/kb_article_chunks.json`

**Expected output:**
- 1000-1500+ atomic chunks from 200 articles
- Average 170 tokens per chunk
- 180,000+ total tokens

---

### **Step 6: Embed & Ingest into Chroma**

```bash
python scripts/ingest_kb_chunks.py
```

**What it does:**
- ✅ Loads KB article chunks
- ✅ Generates OpenAI embeddings (1536-d vectors)
- ✅ Merges with existing 92 atomic chunks
- ✅ Total collection: ~1200+ documents

**Result:**
- Old collection: 92 documents (local KB articles)
- New collection: 92 + 1000+ documents (unified KB)
- Single collection: `acebuddy_kb_v2`

---

### **Step 7: Verify with Smoke Tests**

```bash
python full_smoke_test.py
```

**Expected improvements:**
- Before (92 chunks): 67.4% average confidence
- After (92 + KB chunks): 75-85%+ average confidence
- 4.2x → 5-6x improvement possible

---

## 📊 Expected Results

### **Before Integration**
```
Total documents:      92 (local KB files only)
Average confidence:   67.4%
Coverage:             Limited to 9 local KB topics
```

### **After Integration**
```
Total documents:      1200+ (local + 200 KB articles)
Average confidence:   75-85%+ (estimated)
Coverage:             200+ KB topics + 9 local topics
Improvement:          5-6x better coverage
```

---

## 🔧 Manual Steps (If Automated Scripts Fail)

If any script fails, you can do it manually:

### **Manual Excel Parsing**
```python
import openpyxl
wb = openpyxl.load_workbook('data/SOP_update_sheet.xlsx')
ws = wb.active
for row in ws.iter_rows():
    for cell in row:
        if isinstance(cell.value, str) and cell.value.startswith('http'):
            print(cell.value)
```

### **Manual File Download**
```python
import requests
urls = [...list of URLs from Excel...]
for url in urls:
    response = requests.get(url)
    with open(f"downloads/{url.split('/')[-1]}", 'wb') as f:
        f.write(response.content)
```

### **Manual Text Extraction**
```python
from PyPDF2 import PdfReader
pdf = PdfReader("file.pdf")
text = "".join(page.extract_text() for page in pdf.pages)
```

---

## ⚠️ Troubleshooting

### **Excel file download fails (403 Forbidden)**
**Solution:** Download manually from SharePoint and place in `data/SOP_update_sheet.xlsx`

### **PDF extraction returns empty text**
**Solution:** Some PDFs are scanned images. Use OCR:
```bash
pip install pytesseract
# Requires Tesseract installed on system
```

### **Memory issues with large batch**
**Solution:** Process in smaller batches:
```python
# Chunk processing into groups of 50
for i in range(0, len(files), 50):
    process(files[i:i+50])
```

### **OpenAI API errors**
**Solution:** Check:
1. API key valid: `echo $OPENAI_API_KEY`
2. Account has credits
3. Rate limiting (wait 60s and retry)

---

## 📈 Performance Tips

1. **Parallel Downloads:** Modify `process_kb_articles.py` to use `ThreadPoolExecutor`:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   with ThreadPoolExecutor(max_workers=5) as executor:
       executor.map(download_url, urls)
   ```

2. **Batch Embedding:** Already optimized (batch size = 25)

3. **Incremental Ingestion:** Process in chunks:
   ```python
   # Instead of all at once, do:
   for i in range(0, len(chunks), 500):
       ingest(chunks[i:i+500])
   ```

---

## 📁 File Structure

```
data/
  ├── SOP_update_sheet.xlsx          ← Download manually
  ├── kb_article_links.json          ← Extracted links
  ├── kb_article_chunks.json         ← Final chunks
  ├── kb_downloads/
  │   ├── downloaded/                ← Downloaded files
  │   ├── cleaned/                   ← Cleaned text
  │   ├── download_results.json
  │   └── cleaning_results.json
  └── chroma/                        ← Vector DB (updated)
      └── acebuddy_kb_v2             ← Collection
```

---

## 🎯 Next Steps

1. **Manual Step:** Download Excel file
2. **Run:** `python scripts/process_kb_articles.py`
3. **Run:** `python scripts/chunk_kb_articles.py`
4. **Run:** `python scripts/ingest_kb_chunks.py`
5. **Test:** `python full_smoke_test.py`
6. **Deploy:** System ready for production

**Estimated Time:** 30-60 minutes (depending on file sizes)

---

## 📞 Support

If you encounter issues:
1. Check logs in `data/kb_downloads/` JSON files
2. Verify file sizes are reasonable (not 0 bytes)
3. Check OpenAI API quota
4. Ensure all Python packages installed: `pip install -r requirements.txt`

---

**Status:** Ready for deployment once Excel file is downloaded manually.
