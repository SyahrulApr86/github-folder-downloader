#!/usr/bin/env python3
import os
import sys
import requests
import logging
import time
import random
import base64
from datetime import datetime
import re
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("download_log.txt"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create output directory
OUTPUT_DIR = "github_download"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_github_url(url):
    """Parse a GitHub URL to extract owner, repo, commit, and path."""
    # Pattern for GitHub URLs (https://github.com/owner/repo/tree/commit/path)
    pattern = r'https://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+)(?:/(.*))?'
    match = re.match(pattern, url)

    if not match:
        raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo/tree/commit/path")

    owner = match.group(1)
    repo = match.group(2)
    commit = match.group(3)
    path = match.group(4) or ""  # If path is None, use empty string

    return owner, repo, commit, path


def list_directory_contents(username, repo, path, commit_hash, auth):
    """List the contents of a directory in the GitHub repository using the API."""
    # GitHub API URL for getting directory contents at a specific commit
    api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{path}?ref={commit_hash}"

    try:
        response = requests.get(api_url, auth=auth, timeout=15)

        if response.status_code == 200:
            contents = response.json()
            return contents, True
        else:
            logger.warning(f"Failed to list contents at {path}. Status code: {response.status_code}")
            logger.warning(f"Response: {response.text}")
            return [], False

    except Exception as e:
        logger.error(f"Error listing contents at {path}: {str(e)}")
        return [], False


def download_file(username, repo, file_path, file_name, output_dir, commit_hash, auth):
    """Download a file from GitHub using the API."""
    # GitHub API URL for getting file contents at a specific commit
    api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{file_path}?ref={commit_hash}"
    raw_url = f"https://raw.githubusercontent.com/{username}/{repo}/{commit_hash}/{file_path}"

    logger.info(f"Trying to download: {file_path}")

    try:
        # First try with the GitHub API
        api_response = requests.get(api_url, auth=auth, timeout=15)

        if api_response.status_code == 200:
            try:
                content_data = api_response.json()

                # Check if it's a file (not a directory)
                if isinstance(content_data, dict) and 'type' in content_data and content_data['type'] == 'file':
                    if 'content' in content_data and content_data.get('encoding') == 'base64':
                        # Decode base64 content
                        file_content = base64.b64decode(content_data['content'])

                        # Determine if it's a binary or text file
                        is_binary = False
                        try:
                            file_content.decode('utf-8')
                        except UnicodeDecodeError:
                            is_binary = True

                        # Save the file
                        output_path = os.path.join(output_dir, file_name)
                        mode = 'wb' if is_binary else 'w'

                        with open(output_path, mode, encoding='utf-8' if mode == 'w' else None) as f:
                            if is_binary:
                                f.write(file_content)
                            else:
                                f.write(file_content.decode('utf-8'))

                        logger.info(f"Successfully downloaded {file_name}")
                        return True
                    else:
                        logger.warning(f"Content not found in API response for {file_path}")
                else:
                    logger.warning(f"The path {file_path} is not a file")
            except Exception as e:
                logger.error(f"Error processing API response for {file_path}: {str(e)}")

        # If API method fails, try the raw URL
        logger.info(f"API method failed, trying raw URL: {raw_url}")
        raw_response = requests.get(raw_url, auth=auth, timeout=15)

        if raw_response.status_code == 200:
            # Save the file
            output_path = os.path.join(output_dir, file_name)

            # Try to determine if it's a binary file
            is_binary = False
            try:
                raw_response.content.decode('utf-8')
            except UnicodeDecodeError:
                is_binary = True

            mode = 'wb' if is_binary else 'w'

            with open(output_path, mode, encoding='utf-8' if mode == 'w' else None) as f:
                if is_binary:
                    f.write(raw_response.content)
                else:
                    f.write(raw_response.text)

            logger.info(f"Successfully downloaded {file_name} using raw URL")
            return True

        logger.warning(
            f"Failed to download {file_path}. Status codes: API={api_response.status_code}, Raw={raw_response.status_code}")
        return False

    except Exception as e:
        logger.error(f"Error downloading {file_path}: {str(e)}")
        return False


def process_directory(username, repo, path, output_base_dir, commit_hash, auth):
    """Recursively process a directory and its contents."""
    contents, success = list_directory_contents(username, repo, path, commit_hash, auth)

    if not success:
        return 0

    files_downloaded = 0

    for item in contents:
        # Skip .git directories and other hidden files
        if item['name'].startswith('.'):
            continue

        if item['type'] == 'file':
            # Create output directory if it doesn't exist
            relative_path = path
            output_dir = os.path.join(output_base_dir, relative_path)
            os.makedirs(output_dir, exist_ok=True)

            # Download the file
            if download_file(username, repo, item['path'], item['name'], output_dir, commit_hash, auth):
                files_downloaded += 1

                # Add a small delay to avoid rate limiting
                time.sleep(random.uniform(0.1, 0.5))

        elif item['type'] == 'dir':
            # Recursively process subdirectory
            sub_files = process_directory(username, repo, item['path'], output_base_dir, commit_hash, auth)
            files_downloaded += sub_files

    return files_downloaded


def main():
    # Get GitHub credentials from .env file
    github_username = os.getenv("GITHUB_USERNAME")
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_username or not github_token:
        logger.error("GitHub credentials not found in .env file.")
        logger.error("Please create a .env file with GITHUB_USERNAME and GITHUB_TOKEN variables.")
        print("\nExample .env file content:")
        print("GITHUB_USERNAME=your_username")
        print("GITHUB_TOKEN=your_personal_access_token")
        sys.exit(1)

    # Set authentication
    auth = (github_username, github_token)

    # Test authentication
    logger.info("Testing GitHub authentication...")
    test_url = "https://api.github.com/user"
    try:
        response = requests.get(test_url, auth=auth)
        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"Authentication successful! Logged in as: {user_data.get('login')}")
        else:
            logger.error(f"Authentication failed with status code: {response.status_code}")
            logger.error("Please check your credentials in the .env file and try again.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error testing authentication: {str(e)}")
        sys.exit(1)

    # Get the GitHub URL from user input
    github_url = input("Enter GitHub URL (e.g., https://github.com/owner/repo/tree/commit/path): ")

    try:
        # Parse the GitHub URL
        repo_owner, repo_name, commit_hash, folder_path = parse_github_url(github_url)

        logger.info(f"Repository Owner: {repo_owner}")
        logger.info(f"Repository Name: {repo_name}")
        logger.info(f"Commit Hash: {commit_hash}")
        logger.info(f"Folder Path: {folder_path}")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    start_time = datetime.now()
    logger.info(f"Download operation started at {start_time}")

    # Create a specific output directory for this download
    download_dir = os.path.join(OUTPUT_DIR, f"{repo_name}_{commit_hash[:7]}")
    os.makedirs(download_dir, exist_ok=True)

    # Process the directory
    logger.info(f"Downloading all files from {repo_owner}/{repo_name}/{folder_path} at commit {commit_hash}")
    files_downloaded = process_directory(repo_owner, repo_name, folder_path, download_dir, commit_hash, auth)

    end_time = datetime.now()
    duration = end_time - start_time

    # Print summary
    logger.info(f"Operation completed at {end_time} (Duration: {duration})")
    logger.info("Summary:")
    logger.info(f"- Total files downloaded: {files_downloaded}")

    logger.info("All operations have been completed.")
    logger.info(f"The downloaded files are in the '{download_dir}' directory.")


if __name__ == "__main__":
    print("\nGitHub Folder Downloader")
    print("========================")
    print("This script will download all files from a specific folder in a GitHub repository")
    print("based on the URL you provide.")
    print("Credentials will be loaded from a .env file in the current directory.\n")

    # Check if .env file exists, create a template if it doesn't
    if not os.path.exists(".env"):
        print("Creating a template .env file...")
        with open(".env", "w") as env_file:
            env_file.write("# GitHub credentials\n")
            env_file.write("GITHUB_USERNAME=your_username\n")
            env_file.write("GITHUB_TOKEN=your_personal_access_token\n")
        print(".env file created. Please fill in your GitHub credentials before running again.")
        sys.exit(0)

    # Ask for confirmation before running
    try:
        response = input("Continue with download? (y/n): ").strip().lower()
        if response != 'y':
            print("Script execution cancelled.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nScript execution cancelled.")
        sys.exit(0)

    main()