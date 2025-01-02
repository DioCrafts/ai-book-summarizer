# 📚 AI Book PDF Summarizer: Page-by-Page Knowledge Extractor

The `summarizer.py` script performs an intelligent analysis of PDF books, extracting knowledge points page-by-page and generating well-structured summaries tailored for students and professionals. The script leverages OpenAI's API to ensure concise and clear understanding of the material.

## Features

- 📖 **Automated PDF Analysis**: Extracts key knowledge points.
- 🤖 **AI-Powered Summarization**: Generates Markdown summaries.
- 🎯 **Educational Focus**: Summarizes in simple language for students.
- 📂 **Organized Outputs**: Creates structured folders and files.
- 📝 **Customizable**: Adjust processing intervals and page limits.
- 🌟 **Smart Content Filtering**: Skips irrelevant sections like TOC or acknowledgments.
- 🎨 **Enhanced Readability**: Color-coded terminal output.

---

## Setup Instructions

### 1. Clone the Repository
```bash
# Clone the repository
$ git clone [repository-url]
$ cd [repository-name]
```

### 2. Install Dependencies
Ensure you have Python 3.7+ installed. Install the required libraries:
```bash
$ pip install -r requirements.txt
```

### 3. Set OpenAI API Key
Export your OpenAI API key:
```bash
$ export OPENAI_API_KEY="sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### 4. Configure the Script
- Place your PDF file in the project root.
- Open `summarizer.py` and update the `PDF_NAME` constant with your PDF filename.
- (Optional) Adjust processing parameters such as `TEST_PAGES` or `ANALYSIS_INTERVAL`.

---

## How to Run

1. Run the script:
```bash
$ python summarizer.py
```

2. Follow the on-screen instructions to process your PDF.

3. Outputs will be saved in:
   - `book_analysis/knowledge_bases/`: JSON files with extracted knowledge.
   - `book_analysis/summaries/`: Markdown summaries for each chapter and section.
   - `book_analysis/pdfs/`: A copy of your PDF file.

---

## Example Usage

### Input
Place a PDF named `software-architecture.pdf` in the project root.

### Command
```bash
$ python summarizer.py
```

### Output Directory Structure
```
book_analysis/
├── knowledge_bases/
│   └── software-architecture_knowledge.json
├── summaries/
│   ├── part-i-overview/
│   │   ├── 00-readme.md
│   │   ├── 01-reliability.md
│   │   ├── 02-scalability.md
│   │   └── ...
├── pdfs/
│   └── software-architecture.pdf
```

---

## Configuration Constants

| Constant            | Description                                      |
|---------------------|--------------------------------------------------|
| `PDF_NAME`          | Name of the PDF file to be processed.            |
| `BASE_DIR`          | Base directory for storing outputs.              |
| `TEST_PAGES`        | Limit of pages to process (set `None` for all).  |
| `ANALYSIS_INTERVAL` | Number of pages for interim summaries.           |
| `MODEL`             | OpenAI model used for processing.                |

---

## Functions Overview

### 1. `process_page(client, page_text: str) -> PageContent`
- Processes each page of the PDF.
- Extracts relevant knowledge points using OpenAI API.

### 2. `analyze_knowledge(client, title: str, knowledge_points: list[str]) -> str`
- Summarizes extracted knowledge in Markdown format.

### 3. `setup_directories()`
- Sets up necessary directories for outputs.

### 4. `save_md(folder, prefix, title, markdown_text)`
- Saves generated summaries in Markdown files.

### 5. `main()`
- Orchestrates the script: loads the PDF, processes pages, and saves results.

---

## Notes

- Ensure the API key is valid and has sufficient usage quota.
- The script is optimized for educational PDFs but can process general documents.

---

## Support

If you find this script helpful, consider supporting:

- ⭐ **Contribute**: Submit issues or enhancements on GitHub.
- 💡 **Feedback**: Share your thoughts and improvements.

---

Enjoy using the AI PDF Summarizer!

