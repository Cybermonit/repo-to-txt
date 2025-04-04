# Git Repo to TXT (Enhanced): Consolidate and Filter Repository Content for LLM Analysis

This enhanced Python script takes a repository downloaded as a `.zip` file, processes it, and generates a single, comprehensive `.txt` file. This output file includes:

1. A clean directory structure tree.
2. The concatenated content of text files within the repository.
3. Filtering capabilities to exclude specific files/directories (using glob patterns).
4. An option to limit the inclusion of content from very large files.

**The primary goal remains to prepare codebase information in a format easily consumable by Large Language Models (LLMs), but now with greater control over the generated context.** This is especially useful for models with large context windows (like Gemini 2.5 Pro).

## Table of Contents

- [Why Use This?](#why-use-this)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Command-Line Interface](#command-line-interface)
  - [Command-Line Options](#command-line-options)
  - [Examples](#examples)
- [Output File Format](#output-file-format)
- [Recommended LLM Usage (Leveraging Filtering)](#recommended-llm-usage-leveraging-filtering)
- [How It Works (Updated)](#how-it-works-updated)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [License](#license)

## Why Use This?

Large Language Models excel at understanding code when provided with sufficient context. Feeding them fragmented information limits their analytical capabilities. This script addresses this by:

1. **Consolidating Context:** Packs the directory layout and relevant code into one file.
2. **Filtering Noise:** Allows exclusion of irrelevant files/directories (like `node_modules`, build artifacts, logs, large assets) that consume valuable context window space without adding analytical value.
3. **Managing Size:** Provides an option to skip the content of excessively large files that might otherwise dominate the input.
4. **Simplifying Input:** Makes it easier to provide large codebases to LLMs, overcoming potential limits on file uploads or copy-paste length.
5. **Enabling Holistic Analysis:** Allows LLMs (especially large-context ones) to gain a "bigger picture" view for tasks like architecture explanation, cross-file refactoring, documentation generation, security reviews, and understanding unfamiliar projects.

## Features

- Processes `.zip` archives (typically from GitHub/GitLab "Download ZIP").
- **Command-Line Interface:** Easy to use and integrate into scripts via `argparse`.
- **Configurable Exclusions:** Use glob patterns (`*.log`, `dist/`, `__pycache__/`) via the `-e` / `--exclude` flag to ignore specific files or directories.
- **File Size Limit:** Optionally skip content inclusion for files exceeding a specified size (in KB) using the `-mfs` / `--max-file-size` flag.
- **Verbose Mode:** Enable detailed logging (`-v` / `--verbose`) for better insight into the process and easier debugging.
- Automatically extracts to a temporary directory (securely cleaned up afterwards).
- Detects common nested root folder structures in ZIP downloads.
- Generates a clear, indented directory structure tree (reflecting exclusions).
- Reads and concatenates content of *included* text files.
- Attempts `UTF-8` reading with `Latin-1` fallback and error replacement.
- Identifies and skips content of binary files, clearly marking them.
- Outputs everything into a single `.txt` file (customizable path/name via `-o` / `--output`).
- Cross-platform compatibility (standard Python libraries).

## Requirements

- **Python 3.6 or higher.**
- No external libraries are required (uses only `os`, `zipfile`, `tempfile`, `shutil`, `traceback`, `argparse`, `fnmatch`).

## Installation

1. **Clone the Repository (Recommended):**

   ```
   git clone https://github.com/YOUR_USERNAME/gitrepo-to-txt.git
   cd gitrepo-to-txt

   ```

   (Replace `YOUR_USERNAME` with your actual GitHub username or the original repo path).
2. **Or Download:** Download the `repo_zip_to_txt.py` script directly.
3. **(Optional but Recommended) Use a Virtual Environment:**

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`

   ```

   This isolates the script's environment.

## Usage

### Command-Line Interface

Run the script from your terminal using `python`:

```
python repo_zip_to_txt.py [OPTIONS] INPUT_ZIP_FILE

```

### Command-Line Options

- **`INPUT_ZIP_FILE`** (Required): The path to the input `.zip` file containing the repository.
- **`-o OUTPUT_FILE`, `--output OUTPUT_FILE`** (Optional):
  - Specifies the path and filename for the generated `.txt` file.
  - If omitted, the output filename defaults to `_structure_and_content.txt` saved in the current directory.
- **`-e PATTERN`, `--exclude PATTERN`** (Optional, Repeatable):
  - Specifies a glob pattern for files or directories to exclude.
  - Use standard shell wildcard syntax (e.g., `*.log`, `?emp*`, `[abc]*.txt`, `build/`, `**/node_modules/**`).
  - The pattern is matched against both the file/directory basename and its relative path from the repository root (using `/` as separator).
  - Can be used multiple times to add several exclusion rules (e.g., `-e "*.tmp" -e "dist/"`).
- **`-mfs KB`, `--max-file-size KB`** (Optional):
  - Sets a maximum file size limit in Kilobytes (KB).
  - The *content* of files larger than this limit will be skipped (they will still appear in the structure tree, marked as size-skipped).
  - Example: `-mfs 1024` skips content of files larger than 1 MB.
  - Defaults to `None` (no size limit).
- **`-v`, `--verbose`** (Optional):
  - Enables verbose mode, printing detailed information about each step (unpacking, root detection, exclusions, file reading, saving). Useful for debugging.

### Examples

1. **Basic Usage (Automatic Output Name):**

   ```
   python repo_zip_to_txt.py my-repository-main.zip

   ```

   (Generates `my-repository-main_structure_and_content.txt` in the current folder)
2. **Specify Output File:**

   ```
   python repo_zip_to_txt.py my-repository-main.zip -o ~/Documents/repo_analysis.txt

   ```
3. **Exclude Log Files and Build Directory:**

   ```
   python repo_zip_to_txt.py my-project.zip -e "*.log" -e "build/"

   ```
4. **Exclude `node_modules` (Anywhere) and Temporary Files:**

   ```
   python repo_zip_to_txt.py frontend-app.zip -e "**/node_modules/**" -e "*.tmp"

   ```
5. **Limit File Content Size to 500KB and Use Verbose Mode:**

   ```
   python repo_zip_to_txt.py data-processing-repo.zip -mfs 500 -v

   ```
6. **Combined Options:**

   ```
   python repo_zip_to_txt.py complex-project.zip -o analysis.txt -e "docs/" -e "*.test.js" -e "coverage/" -mfs 2048 -v

   ```

## Output File Format

The generated `.txt` file has a consistent structure:

1. **Header:** Indicates the source ZIP file. May include lines detailing applied exclusion patterns and size limits if used.
2. **Directory Structure Section:**
   - Starts with `DIRECTORY STRUCTURE:`
   - Shows a tree view of *included* directories and files.
   - Ends with a summary (`Included directories: X, Included files: Y, Excluded dirs: Z, Excluded files: W`).
3. **File Contents Section:**
   - Starts with `FILE CONTENTS:`
   - For each *included* text file (respecting size limits):
     - Header: `--- BEGIN FILE: path/to/your/file.py ---`
     - Full content (if not binary and within size limit).
     - Or a skip message:
       - `[Binary file - content skipped]`
       - `[File content skipped - size (XXX.X KB) exceeds limit (YYY KB)]`
     - Encoding warnings/errors if applicable (`[WARNING: Could not read as UTF-8...]`, `[Error reading file...]`).
     - Footer: `--- END FILE: path/to/your/file.py ---`

```
Repository structure and content from file: my-project.zip
Applied exclusion patterns: *.log, build/
Applied max file size limit: 500 KB
================================================================================

DIRECTORY STRUCTURE:
--------------------------------------------------------------------------------
my-project/
  |-- .gitignore
  |-- README.md
  |-- src/
  |  |-- __init__.py
  |  |-- main.py
  |  |-- data/
  |  |  |-- large_data_file.csv
  |-- assets/
  |  |-- logo.png
  # build/ directory excluded
  # server.log excluded

(Included directories: 3, Included files: 5, Excluded dirs: 1, Excluded files: 1)

================================================================================

FILE CONTENTS:
--------------------------------------------------------------------------------

--- BEGIN FILE: .gitignore ---
build/
*.log
__pycache__/
--- END FILE: .gitignore ---

--- BEGIN FILE: README.md ---
# My Project
...
--- END FILE: README.md ---

... [Content of src/__init__.py, src/main.py] ...

--- BEGIN FILE: src/data/large_data_file.csv ---
[File content skipped - size (750.2 KB) exceeds limit (500 KB)]
--- END FILE: src/data/large_data_file.csv ---

--- BEGIN FILE: assets/logo.png ---
[Binary file - content skipped]
--- END FILE: assets/logo.png ---


```

## Recommended LLM Usage (Leveraging Filtering)

The true power comes when feeding this consolidated, *filtered* output to advanced LLMs.

**Recommendation: Google Gemini 1.5 Pro (or similar large-context models)**

- Models like **Gemini 1.5 Pro** (with its up to 1M token context window) or **Claude 3 Opus** (200k tokens) are ideal.
- **Benefit of Filtering:** By using `--exclude` and `--max-file-size`, you create a more focused input for the LLM. This:
  - **Reduces Noise:** Prevents irrelevant code (dependencies, logs, large assets) from cluttering the context.
  - **Saves Tokens:** Makes analysis more efficient and potentially cheaper/faster by using fewer tokens.
  - **Improves Relevance:** Helps the LLM focus on the core application logic.
- **How to Use:** Copy the *entire* content of the generated `.txt` file and paste it into your prompt.

**Example Prompt Structure (Focusing Analysis):**

```
Analyze the following repository structure and code, prepared from a ZIP archive. Irrelevant files/directories (like build artifacts, logs, vendor code specified via exclusions) and content of files exceeding 500KB have been omitted.

[PASTE THE ENTIRE CONTENT of the generated .txt file here]

Based ONLY on the provided code and structure:
1. Describe the main function of the `src/main.py` script.
2. Identify any potential dependencies between modules in the `src/` directory.
3. Suggest improvements for error handling within the included Python files.
4. Generate a summary of the project's purpose based on the README and core source files.

```

## How It Works (Updated)

1. **Argument Parsing:** Parses command-line arguments (`input_zip`, `-o`, `-e`, `-mfs`, `-v`).
2. **Input Validation:** Checks ZIP file existence.
3. **Temporary Extraction:** Extracts ZIP contents to a temporary directory.
4. **Root Directory Detection:** Identifies the main repository folder within the extracted files.
5. **Directory Walk & Filtering:** Uses `os.walk()`. Before processing files/subdirs in a directory:
   - Checks if the directory or file matches any `--exclude` patterns using `fnmatch`.
   - If excluded, it's skipped, and counts are updated.
6. **Structure Generation:** Builds the indented directory structure string, only including non-excluded items.
7. **File Processing:** For each non-excluded file:
   - Checks if its size exceeds `--max-file-size` (if set). Skips content if too large.
   - Checks if it's likely binary (looks for null bytes). Skips content if binary.
   - If text and within size limits, reads content (UTF-8 -> Latin-1 fallback).
   - Stores content or skip messages.
8. **Concatenation:** Combines header, structure, summaries, and all collected file contents/messages.
9. **Output Writing:** Saves the final string to the specified output `.txt` file (UTF-8 encoded). Creates the output directory if needed.
10. **Cleanup:** Automatically removes the temporary directory.

## Limitations

- **Glob Pattern Complexity:** Very complex glob patterns might behave unexpectedly; standard use cases are well-supported.
- **Binary Detection:** Heuristic-based (null byte check); might misclassify some rare text file formats as binary or vice-versa.
- **Encoding:** Handles UTF-8 and Latin-1 well, but exotic encodings might still cause read errors (shown in output).
- **Performance:** Processing very large repositories with millions of small files might be slow.
- **Output Size:** Even with filtering, large codebases can generate huge TXT files, potentially exceeding LLM context limits (though filtering helps significantly).
- **No Code Understanding:** The script only concatenates text; it doesn't parse or understand the code's semantics.

## Troubleshooting

- **"File not found" Error:** Double-check the path to the input `.zip` file. Ensure correct spelling and that the file exists.
- **Permission Denied (Output):** Ensure you have write permissions in the directory where the output file is being saved. Try specifying an output path in a directory you own (e.g., `-o ~/output.txt`).
- **Incorrect Exclusions:** Review your glob patterns (`-e`). Use `-v` to see which files are being matched by which patterns. Remember patterns match relative paths and basenames. Use `/` for path separators in patterns.
- **File Content Garbled/Missing:** Check the output for encoding warnings or read errors. The file might use an unsupported encoding, or it might have been skipped due to size/binary detection. Use `-v` for details.
- **BadZipFile Error:** The input `.zip` file might be corrupted or incomplete. Try downloading it again.

## Security Considerations

The generated `.txt` file contains a significant portion (or all) of the repository's source code. If the original repository contains sensitive information (API keys, passwords, private logic), the output file will also contain it.

- **Treat the output `.txt` file with the same level of confidentiality as the original source code.**
- **Do not share the output file publicly or with untrusted parties if the code is private.**
- **Be mindful when pasting the content into third-party LLM services; review their data usage and privacy policies.**

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
