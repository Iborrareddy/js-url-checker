# Js-Url-Checker 🛡️ : Bulk JavaScript URL Validator
A high-performance, dependency-free Python tool to validate and download JavaScript assets in bulk.

`js-url-checker` is designed for security researchers, developers, and web archivists who need to verify large lists of JavaScript URLs. It efficiently distinguishes between live scripts and dead links, handles redirects, and helps ensure that what you download is actually JavaScript, not a masked “Access Denied” HTML page.

<img width="2750" height="1092" alt="Gemini_Generated_Image_nvcte9nvcte9nvct" src="https://github.com/user-attachments/assets/98ab5927-971d-41a5-964a-0a6eb88cb61e" />


## ✨ Key Features
- ⚡ **High Concurrency**: Uses multi-threading to process many URLs quickly.
- 🔍 **Smart Probing**: Performs a `HEAD` request first, with automatic `GET` fallback.
- 🔄 **Resilience**: Retries + exponential backoff to handle flaky connections and rate limiting.
- 🛡️ **Content Verification**: Optional strict checks for JavaScript Content-Type headers.
- 💾 **Safe Downloads**: Avoids saving HTML error pages (403/404 screens) as `.js` files.
- 📊 **Comprehensive Reporting**: Generates clean `.txt` lists and a detailed `report.csv`.
- 🪶 **Zero Dependencies**: Built entirely on Python’s standard library. No `pip install`.

## 🚀 Getting Started

### 1) Prerequisites
- Python **3.8+**

### 2) Installation
Clone the repository:
```bash
git clone https://github.com/Iborrareddy/js-url-checker.git
cd js-url-checker
```
### 3) Prepare Input

Create a file named `js_files.txt` and add your URLs (one per line).  
Use `#` for comments or to disable URLs.

```txt
https://cdn.example.com/js/main.js
https://website.com/assets/app.min.js?v=1.2
# https://old-site.com/broken.js
```


## 📖 Usage
### Basic validation
```bash
python3 checker.py -i js_files.txt
```
### Use more/less workers
```bash
python3 checker.py -i js_files.txt -w 30
```

### Increase timeout
```bash
python3 checker.py -i js_files.txt -t 20
```
### Enable stricter JS header checks
```bash
python3 checker.py -i js_files.txt --check-js-header
```
### Download active JS files
```bash
python3 checker.py -i js_files.txt --download --outdir active_js_downloads
```
### Change CSV report file name
```bash
python3 checker.py -i js_files.txt --csv results.csv
```
### ⚖️ Disclaimer
```bash
This project is intended for educational and authorized security testing purposes only. The author is not responsible for misuse or damage caused by this tool. Use responsibly and within legal boundaries.
```
