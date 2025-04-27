# GitHub Folder Downloader

A Python script to **download specific folders or files from a GitHub repository** based on a given commit URL.

This tool supports:
- Recursive downloading of all files in a folder
- Authentication using GitHub Personal Access Tokens (PAT)
- Handling of both text and binary files
- Detailed logging of download operations

---

## Features

- Download the contents of a folder or individual files from a GitHub repository at a specific commit
- Automatic detection and handling of text and binary files
- Fallback to raw GitHub URLs if the API method fails
- Authentication support to prevent GitHub API rate limiting
- Detailed logging to both console and a `download_log.txt` file
- Automatic creation of a `.env` template if one does not exist

---

## Installation

1. Clone this repository:
```bash
git clone https://github.com/SyahrulApr86/github-folder-downloader.git
cd github-folder-downloader
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory (or run the script once to automatically generate a template):
```dotenv
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_token
```
You can generate a [GitHub Personal Access Token](https://github.com/settings/tokens) with at least `repo` and `read:packages` scopes.

---

## Usage

Run the script:

```bash
python github_folder_downloader.py
```

You will be prompted to input a GitHub URL. Example:

```
https://github.com/owner/repo/tree/commit-hash/path/to/folder
```

The script will:

- Authenticate with GitHub using your credentials
- Attempt to download all files recursively from the specified path
- Save the downloaded content in a directory under `github_download/repo_commit/`

Example input:

```
Enter GitHub URL (e.g., https://github.com/owner/repo/tree/commit/path):
https://github.com/octocat/Hello-World/tree/6b8f3b4/src
```

---

## Requirements

- Python 3.7 or later
- The following Python packages:
  - `requests`
  - `python-dotenv`

Example `requirements.txt`:
```
requests
python-dotenv
```

---

## Notes

- Only URLs pointing to a specific commit are supported, for example:
  ```
  https://github.com/owner/repo/tree/commit/path
  ```
  or
  ```
  https://github.com/owner/repo/blob/commit/path/to/file
  ```

- This script **does not clone** the entire repository, it only downloads the specified folder or file.

- Authentication is strongly recommended to avoid GitHub API rate limits for unauthenticated requests.

---

## Future Improvements

- Add support for downloading from branches without specifying a commit hash
- Implement a progress indicator for downloads
- Add retry logic for failed downloads
- Support for parallel downloads

---

## License

This project is licensed under the MIT [License](LICENSE).
