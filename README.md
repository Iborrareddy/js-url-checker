# js-url-checker 🛡️  
A high-performance, dependency-free Python tool to validate and download JavaScript assets in bulk.

`js-url-checker` is designed for security researchers, developers, and web archivists who need to verify large lists of JavaScript URLs. It efficiently distinguishes between live scripts and dead links, handles redirects, and helps ensure that what you download is actually JavaScript, not a masked “Access Denied” HTML page.

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
git clone https://github.com/yourusername/js-url-checker.git
cd js-url-checker





