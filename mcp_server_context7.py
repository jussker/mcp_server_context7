#!/usr/bin/env python3
"""
Context7 MCP Server

An MCP server that provides access to Context7 API for searching and downloading
library documentation and source repositories. This server exposes Context7
functionality through the Model Context Protocol interface.

Based on the Context7 project: https://github.com/upstash/context7/

The MIT License (MIT)

Copyright (c) 2021 Upstash, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

import json
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastmcp import FastMCP

# Configuration
# Load package version from the mcp package to report server version in headers
_THIS_DIR = os.path.dirname(__file__)
_MCP_PKG_JSON = os.path.join(
    _THIS_DIR, "context7", "packages", "mcp", "package.json"
)
try:
    with open(_MCP_PKG_JSON, encoding="utf-8") as _f:
        _pkg = json.load(_f)
        SERVER_VERSION = _pkg.get("version", "0.0.0")
except Exception:
    SERVER_VERSION = "0.0.0"

CONTEXT7_API_BASE_URL = os.environ.get(
    "CONTEXT7_API_URL", "https://context7.com/api"
)

# Encryption key (hex 64 chars / 32 bytes)
DEFAULT_ENCRYPTION_KEY = (
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
)
ENCRYPTION_KEY = os.environ.get("CLIENT_IP_ENCRYPTION_KEY", DEFAULT_ENCRYPTION_KEY)

# Proxy configuration (respect various env var casings)
PROXY_URL = (
    os.environ.get("HTTPS_PROXY")
    or os.environ.get("https_proxy")
    or os.environ.get("HTTP_PROXY")
    or os.environ.get("http_proxy")
    or None
)
PROXY_CONFIG = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else {}

# Create the MCP server
mcp = FastMCP("Context7 MCP Server 📚")


# Utility functions from original context7_tool.py
def validate_encryption_key(key: str) -> bool:
    """Validate that the encryption key is 64 hex characters (32 bytes)."""
    return bool(re.match(r"^[0-9a-fA-F]{64}$", key))


def encrypt_client_ip(client_ip: str) -> str:
    """Encrypts the client IP using AES-256-CBC."""
    if not validate_encryption_key(ENCRYPTION_KEY):
        return client_ip

    try:
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(bytes.fromhex(ENCRYPTION_KEY)),
            modes.CBC(iv),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(client_ip.encode("utf-8")) + encryptor.finalize()
        return f"{iv.hex()}:{encrypted.hex()}"
    except Exception:
        return client_ip


def generate_headers(
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Generate headers for Context7 API requests.

    Accepts either None, a simple dict like {"clientIp": "1.2.3.4"}, or
    legacy usage where a string IP was passed (handled by callers).
    """
    ctx = context or {}
    # Backwards-compatible: if a plain string was passed, treat as clientIp
    if isinstance(ctx, str):
        ctx = {"clientIp": ctx}

    headers: Dict[str, str] = {
        "X-Context7-Source": "mcp-server",
        "X-Context7-Server-Version": SERVER_VERSION,
    }

    client_ip = ctx.get("clientIp") or ctx.get("client_ip")
    if client_ip:
        headers["mcp-client-ip"] = encrypt_client_ip(client_ip)

    api_key = ctx.get("apiKey") or ctx.get("api_key")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    client_info = ctx.get("clientInfo") or ctx.get("client_info") or {}
    if isinstance(client_info, dict):
        ide = client_info.get("ide")
        version = client_info.get("version")
        if ide:
            headers["X-Context7-Client-IDE"] = ide
        if version:
            headers["X-Context7-Client-Version"] = version

    transport = ctx.get("transport")
    if transport:
        headers["X-Context7-Transport"] = transport

    return headers


def extract_github_repo_from_doc(text: str) -> Optional[str]:
    """Extract GitHub repository URL from the first 50 lines of documentation text."""
    lines = text.split("\n")[:50]
    text_to_check = "\n".join(lines)

    github_patterns = [
        r"https://github\.com/([^/\s]+/[^/\s]+)",
        r"SOURCE:\s*https://github\.com/([^/\s]+/[^/\s]+)",
        r"github\.com/([^/\s]+/[^/\s]+)",
    ]

    for pattern in github_patterns:
        matches = re.findall(pattern, text_to_check)
        if matches:
            repo_path = matches[0]
            if repo_path.endswith(".git"):
                repo_path = repo_path[:-4]
            return f"https://github.com/{repo_path}"

    return None


def format_search_results(search_response: Dict[str, Any]) -> str:
    """Formats a search response into a human-readable string.

    Aligns with the TypeScript `formatSearchResults` behavior: maps trustScore to
    a reputation label and includes benchmarkScore when available.
    """
    results = search_response.get("results", [])
    if not results:
        return "No documentation libraries found matching your query."

    def _reputation_label(score: Optional[int]) -> str:
        if score is None or score < 0:
            return "Unknown"
        if score >= 7:
            return "High"
        if score >= 4:
            return "Medium"
        return "Low"

    formatted_list = []
    for result in results:
        formatted_result = [
            f"- Title: {result.get('title', 'N/A')}",
            f"- Context7-compatible library ID: {result.get('id', 'N/A')}",
            f"- Description: {result.get('description', 'N/A')}",
        ]

        total_snippets = result.get("totalSnippets")
        if total_snippets is not None and total_snippets != -1:
            formatted_result.append(f"- Code Snippets: {total_snippets}")

        reputation = _reputation_label(result.get("trustScore"))
        formatted_result.append(f"- Source Reputation: {reputation}")

        benchmark = result.get("benchmarkScore")
        if benchmark is not None and benchmark > 0:
            formatted_result.append(f"- Benchmark Score: {benchmark}")

        versions = result.get("versions") or []
        if versions:
            formatted_result.append(f"- Versions: {', '.join(versions)}")

        formatted_list.append("\n".join(formatted_result))

    return "\n----------\n".join(formatted_list)


def update_index_file(
    base_dir: str,
    library_id: str,
    doc_file: str,
    repo_dir: Optional[str] = None,
    search_query: Optional[str] = None,
) -> None:
    """
    Updates the INDEX.md file in the km-base directory with information about the downloaded documentation.

    Args:
        base_dir (str): The base directory path (.kms/context7/km-base)
        library_id (str): The Context7 library ID
        doc_file (str): Path to the documentation file
        repo_dir (Optional[str]): Path to the cloned repository directory if available
        search_query (Optional[str]): The original search query used to find this library
    """
    index_path = os.path.join(base_dir, "INDEX.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create entry for this library
    entry_lines = [
        f"## {library_id}",
        f"- **Added**: {timestamp}",
        f"- **Documentation**: `{os.path.basename(doc_file)}`",
    ]

    if repo_dir and os.path.exists(repo_dir):
        entry_lines.append(f"- **Repository**: `{os.path.basename(repo_dir)}/`")

    if search_query:
        entry_lines.append(f'- **Search Query**: "{search_query}"')

    entry_lines.extend(["", "---", ""])
    entry_text = "\n".join(entry_lines)

    # Read existing index file or create header
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            existing_content = f.read()

        # Check if this library already exists in the index
        if f"## {library_id}" in existing_content:
            # Update existing entry
            pattern = rf"## {re.escape(library_id)}.*?(?=## |\Z)"
            updated_content = re.sub(
                pattern, entry_text.rstrip() + "\n\n", existing_content, flags=re.DOTALL
            )
            final_content = updated_content
        else:
            # Add new entry after the header
            lines = existing_content.split("\n")
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith("## ") and "Knowledge Base Index" not in line:
                    header_end = i
                    break
            else:
                header_end = len(lines)

            lines.insert(header_end, entry_text)
            final_content = "\n".join(lines)
    else:
        # Create new index file
        header = [
            "# Knowledge Base Index",
            "",
            f"Last updated: {timestamp}",
            "",
            "This file contains an index of all downloaded documentation and repositories.",
            "",
            "---",
            "",
            entry_text,
        ]
        final_content = "\n".join(header)

    # Write updated content
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(final_content)


def clone_repository(repo_url: str, target_dir: str) -> bool:
    """Clone a GitHub repository to the specified target directory."""
    try:
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        env = os.environ.copy()

        # Add proxy settings to environment for git commands
        env.update(
            {
                "http_proxy": PROXY_CONFIG["http"],
                "https_proxy": PROXY_CONFIG["https"],
                "HTTP_PROXY": PROXY_CONFIG["http"],
                "HTTPS_PROXY": PROXY_CONFIG["https"],
                "all_proxy": "socks5://127.0.0.1:8890",
            }
        )

        if os.path.exists(target_dir):
            if os.path.exists(os.path.join(target_dir, ".git")):
                result = subprocess.run(
                    ["git", "-C", target_dir, "pull", "--depth=1"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env,
                )
                if result.returncode == 0:
                    return True
                else:
                    shutil.rmtree(target_dir)
            else:
                shutil.rmtree(target_dir)

        result = subprocess.run(
            ["git", "clone", "--depth=1", "--single-branch", repo_url, target_dir],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )

        return result.returncode == 0

    except Exception:
        return False


# Internal implementation functions (not decorated with @mcp.tool)
def _search_libraries_impl(
    query: str,
    library_name: Optional[str] = None,
    client_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Internal implementation of search_libraries aligned with v2 API."""
    try:
        url = f"{CONTEXT7_API_BASE_URL}/v2/libs/search"
        params: Dict[str, str] = {"query": query}
        if library_name:
            params["libraryName"] = library_name

        headers = generate_headers(client_context)

        response = requests.get(url, params=params, headers=headers, proxies=PROXY_CONFIG)
        if response.status_code != 200:
            # Try to parse server message
            try:
                msg = response.json().get("message")
            except Exception:
                msg = None
            if response.status_code == 429:
                return {"results": [], "error": "Rate limited. Please try again later."}
            return {"results": [], "error": msg or f"Request failed with status {response.status_code}"}

        search_response = response.json()
        results = search_response.get("results", [])

        if not results:
            return {"message": "No documentation libraries found matching your query.", "results": []}

        # Normalize results
        formatted_results = []
        for result in results:
            formatted_result = {
                "title": result.get("title", "N/A"),
                "id": result.get("id", "N/A"),
                "description": result.get("description", "N/A"),
            }
            if result.get("totalSnippets") is not None:
                formatted_result["totalSnippets"] = result.get("totalSnippets")
            if result.get("trustScore") is not None:
                formatted_result["trustScore"] = result.get("trustScore")
            if result.get("benchmarkScore") is not None:
                formatted_result["benchmarkScore"] = result.get("benchmarkScore")
            if result.get("versions"):
                formatted_result["versions"] = result.get("versions")
            formatted_results.append(formatted_result)

        return {
            "message": f"Found {len(formatted_results)} libraries matching '{query}'",
            "results": formatted_results,
            "formatted_text": format_search_results({"results": formatted_results}),
        }

    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def _fetch_library_documentation_impl(
    library_id: str,
    query: Optional[str] = None,
    tokens: Optional[int] = None,
    client_context: Optional[Dict[str, Any]] = None,
    save_to_file: bool = True,
    sync_repo: bool = False,
    search_query: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal implementation aligned with v2 context API.

    Uses `/v2/context` endpoint which expects `query` and `libraryId`.
    """
    try:
        # Normalize library id (strip leading slash)
        if library_id.startswith("/"):
            library_id = library_id[1:]

        url = f"{CONTEXT7_API_BASE_URL}/v2/context"
        params: Dict[str, str] = {"libraryId": library_id, "query": query or ""}
        if tokens:
            params["tokens"] = str(tokens)

        headers = generate_headers(client_context)

        response = requests.get(url, params=params, headers=headers, proxies=PROXY_CONFIG)
        if response.status_code != 200:
            try:
                msg = response.json().get("message")
            except Exception:
                msg = None
            if response.status_code == 429:
                return {"error": "Rate limited. Please try again later."}
            return {"error": msg or f"Request failed with status {response.status_code}"}

        text = response.text
        if not text:
            return {"error": "Documentation not found or not finalized for this library."}

        result = {
            "library_id": library_id,
            "content": text,
            "length": len(text),
            "query": query,
            "tokens_requested": tokens,
        }

        if save_to_file:
            # Create output directory
            output_dir = ".kms/context7/km-base"
            os.makedirs(output_dir, exist_ok=True)

            safe_id = library_id.replace("/", "_").replace("-", "_")
            output_path = os.path.join(output_dir, f"{safe_id}.md")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            result["saved_to"] = output_path

            # Handle repository sync (try to detect GitHub repo in top of doc)
            if sync_repo:
                repo_url = extract_github_repo_from_doc(text)
                if repo_url:
                    repo_dir = os.path.join(output_dir, f"{safe_id}_repo")
                    if clone_repository(repo_url, repo_dir):
                        result["repo_cloned"] = repo_dir
                        result["repo_url"] = repo_url
                    else:
                        result["repo_clone_failed"] = repo_url
                else:
                    result["no_repo_found"] = "No GitHub repository URL found in documentation"

            repo_dir_for_index = None
            if sync_repo and "repo_cloned" in result:
                repo_dir_for_index = result["repo_cloned"]

            update_index_file(
                base_dir=output_dir,
                library_id=f"/{library_id}",
                doc_file=output_path,
                repo_dir=repo_dir_for_index,
                search_query=search_query,
            )

        return result

    except Exception as e:
        return {"error": f"Failed to fetch documentation: {str(e)}"}


# MCP Tools (these are the decorated versions for MCP server)
@mcp.tool
def search_libraries(
    query: str, library_name: Optional[str] = None, client_ip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Searches for libraries matching the given query using Context7 API.

    This function performs a semantic search across Context7's library database
    to find relevant documentation libraries based on the provided query string.

    Args:
        query (str): The search query string. Can be library names, keywords,
                    descriptions, or any text related to the library you're looking for.
                    Examples: "gradio", "machine learning UI", "fastapi web framework"
        client_ip (Optional[str]): Optional client IP address to include in request headers.
                                  If provided, will be encrypted using AES-256-CBC before sending.
                                  This can help with regional content optimization.

    Returns:
        Dict[str, Any]: Search results dictionary containing:
            - 'message': Status message about the search results
            - 'results': List of matching libraries, each with:
                - 'title': Library name/title
                - 'id': Context7-compatible library ID (format: /org/project)
                - 'description': Brief description of the library
                - 'totalSnippets': Number of available code snippets (-1 if not available)
                - 'trustScore': Trust score rating (-1 if not available)
                - 'versions': List of available versions (if applicable)
            - 'error': Error message if the search fails due to network issues, rate limiting, or API errors.

    Handoff:
        - Use the returned library IDs with fetch_library_documentation() to get full documentation
        - The 'id' field is required for subsequent fetch operations
        - Filter results by 'trustScore' and 'totalSnippets' for quality assessment
        - Handle error responses gracefully (network/API failures)

    Example:
        results = search_libraries("gradio machine learning")
        if results and results.get('results'):
            for lib in results['results']:
                print(f"Found: {lib['title']} - {lib['id']}")
    """
    # Backwards-compatible: if caller passed only client_ip, convert to context
    client_ctx = {"clientIp": client_ip} if client_ip else None
    return _search_libraries_impl(query, library_name, client_ctx)


@mcp.tool
def fetch_library_documentation(
    library_id: str,
    topic: Optional[str] = None,
    tokens: Optional[int] = None,
    client_ip: Optional[str] = None,
    save_to_file: bool = True,
    sync_repo: bool = False,
    search_query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetches comprehensive documentation for a specific library and optionally syncs its source code repository.

    This function retrieves detailed documentation from Context7's database for a given library,
    saves it to a file, and can automatically clone the associated GitHub repository for source code access.

    Args:
        library_id (str): Context7-compatible library identifier (e.g., "/gradio-app/gradio", "/tiangolo/fastapi").
                         Should be obtained from search_libraries() results. Leading slash is optional.

        topic (Optional[str]): Optional topic filter to focus documentation on specific areas.
                              Examples: "installation", "api", "examples", "deployment"

        tokens (Optional[int]): Maximum number of tokens to retrieve from documentation.
                               Controls the length/detail of returned content. Higher values = more content.

        client_ip (Optional[str]): Optional client IP for request headers (encrypted before sending).
                                  Can improve regional content relevance.

        save_to_file (bool): Whether to save documentation to file. Default True.
                            If True, saves to default location: ".kms/context7/km-base/{sanitized_library_id}.md"

        sync_repo (bool): If True, automatically detects and clones the GitHub repository mentioned
                         in the documentation's first 50 lines. Uses shallow clone (--depth=1) to minimize download size.
                         Creates repository directory as "{doc_filename}_repo" alongside the documentation file.

        search_query (Optional[str]): The original search query used to find this library.
                                    This will be recorded in the INDEX.md file for tracking purposes.

    Returns:
        Dict[str, Any]: Dictionary with documentation content and metadata:
            - 'library_id': The processed library identifier
            - 'content': Full documentation text content
            - 'length': Character count of the documentation
            - 'topic': Applied topic filter (if any)
            - 'tokens_requested': Number of tokens requested (if specified)
            - 'saved_to': File path where documentation was saved (if save_to_file=True)
            - 'repo_cloned': Directory path of cloned repository (if sync_repo=True and successful)
            - 'repo_url': GitHub repository URL that was cloned (if sync_repo=True and successful)
            - 'repo_clone_failed': Repository URL that failed to clone (if sync_repo=True and failed)
            - 'no_repo_found': Message if no GitHub URL found in documentation (if sync_repo=True)
            - 'error': Error message if operation failed

    Side Effects:
        - Creates directories as needed for output files
        - Downloads and saves documentation file (.md format)
        - If sync_repo=True and GitHub URL found:
            - Clones repository using shallow clone (latest commit only)
            - If repository exists, attempts to pull latest changes
            - Passes current environment proxy settings to git commands

    Handoff:
        - Documentation file will be in Markdown format with code snippets and examples
        - Repository directory (if created) contains the latest source code
        - Use the documentation file for API reference and examples
        - Use the repository for deeper code analysis and contribution
        - Both files are stored in .kms/context7/km-base/ by default for organized knowledge management

    Error Handling:
        - Gracefully handles network failures, API rate limits, and git clone errors
        - Returns error information in result dictionary without raising exceptions
        - Continues execution even if repository cloning fails

    Example:
        # Basic usage - just get documentation
        result = fetch_library_documentation("gradio-app/gradio")

        # Advanced usage - with repository sync and custom topic
        result = fetch_library_documentation(
            library_id="tiangolo/fastapi",
            topic="api",
            tokens=5000,
            sync_repo=True
        )
    """
    # Map previous arguments to v2 context API: use `search_query` (or topic)
    query = search_query or topic or ""
    client_ctx = {"clientIp": client_ip} if client_ip else None
    return _fetch_library_documentation_impl(
        library_id,
        query=query,
        tokens=tokens,
        client_context=client_ctx,
        save_to_file=save_to_file,
        sync_repo=sync_repo,
        search_query=search_query,
    )


@mcp.tool
def list_downloaded_libraries(
    base_dir: str = ".kms/context7/km-base",
) -> Dict[str, Any]:
    """
    List all previously downloaded library documentation files and their metadata.

    This function scans the specified directory for downloaded library documentation files
    and returns comprehensive information about each library including file metadata and
    associated repository information.

    Args:
        base_dir (str): Directory path where documentation files are stored.
                       Default: ".kms/context7/km-base"
                       This should be the same directory used by fetch_library_documentation()

    Returns:
        Dict[str, Any]: Dictionary containing library inventory information:
            - 'message': Status message indicating number of libraries found
            - 'base_directory': The directory that was scanned for libraries
            - 'libraries': List of library information dictionaries, each containing:
                - 'filename': Name of the documentation file (e.g., "gradio_app_gradio.md")
                - 'library_id': Reconstructed library ID (e.g., "gradio/app/gradio")
                - 'size': File size in bytes
                - 'modified': ISO format timestamp of last modification
                - 'has_repository': Boolean indicating if associated repository directory exists
            - 'error': Error message if operation failed

    Side Effects:
        - Reads directory contents and file metadata
        - Does not modify any files or directories

    Handoff:
        - Use 'filename' values with get_library_content() to read documentation content
        - Use 'library_id' values with fetch_library_documentation() to refresh documentation
        - Filter by 'modified' timestamp to find recently updated libraries
        - Check 'has_repository' to identify libraries with cloned source code

    Error Handling:
        - Returns empty library list if directory doesn't exist
        - Gracefully handles file system errors without raising exceptions
        - Skips files that cannot be read due to permission issues

    Example:
        # List all downloaded libraries
        inventory = list_downloaded_libraries()
        if inventory.get('libraries'):
            for lib in inventory['libraries']:
                print(f"Library: {lib['library_id']} - Size: {lib['size']} bytes")
                if lib['has_repository']:
                    print(f"  └─ Has source code repository")

        # Use custom directory
        custom_inventory = list_downloaded_libraries("/path/to/custom/docs")
    """
    try:
        if not os.path.exists(base_dir):
            return {"message": "No documentation directory found", "libraries": []}

        libraries = []
        for filename in os.listdir(base_dir):
            if filename.endswith(".md") and filename != "INDEX.md":
                filepath = os.path.join(base_dir, filename)
                stat = os.stat(filepath)

                # Check for associated repo directory
                repo_dir = os.path.join(base_dir, filename[:-3] + "_repo")
                has_repo = os.path.exists(repo_dir)

                libraries.append(
                    {
                        "filename": filename,
                        "library_id": filename[:-3].replace("_", "/"),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "has_repository": has_repo,
                    }
                )

        return {
            "message": f"Found {len(libraries)} downloaded libraries",
            "base_directory": base_dir,
            "libraries": libraries,
        }

    except Exception as e:
        return {"error": f"Failed to list libraries: {str(e)}"}


@mcp.tool
def get_library_content(
    filename: str, base_dir: str = ".kms/context7/km-base", max_chars: int = 10000
) -> Dict[str, Any]:
    """
    Retrieve the content of a previously downloaded library documentation file.

    This function reads and returns the content of a specific library documentation file
    that was previously downloaded using fetch_library_documentation(). The content can
    be truncated to avoid overwhelming output while still providing useful information.

    Args:
        filename (str): Name of the documentation file to read.
                       Should be obtained from list_downloaded_libraries() results.
                       Examples: "gradio_app_gradio.md", "tiangolo_fastapi.md"

        base_dir (str): Directory path where documentation files are stored.
                       Default: ".kms/context7/km-base"
                       Should match the directory used by fetch_library_documentation()

        max_chars (int): Maximum number of characters to return in the content field.
                        Default: 10000
                        Used to prevent overwhelming output with very large documentation files.
                        If content exceeds this limit, it will be truncated with a note.

    Returns:
        Dict[str, Any]: Dictionary containing file content and metadata:
            - 'filename': Name of the file that was read
            - 'content': Text content of the documentation file (possibly truncated)
            - 'full_length': Total character count of the original file
            - 'truncated': Boolean indicating if content was truncated due to max_chars limit
            - 'max_chars': The maximum character limit that was applied
            - 'error': Error message if file could not be read

    Side Effects:
        - Reads file content from disk
        - Does not modify the file or directory structure

    Handoff:
        - Use the returned content for analysis, summarization, or display
        - Check 'truncated' field to determine if full content was returned
        - Use 'full_length' to understand the complete size of the documentation
        - If truncated, consider calling again with higher max_chars for full content

    Error Handling:
        - Returns error message if file doesn't exist in specified directory
        - Gracefully handles file reading errors (permissions, encoding issues)
        - Does not raise exceptions for missing or unreadable files

    Example:
        # Read a specific library's documentation
        content = get_library_content("gradio_app_gradio.md")
        if not content.get('error'):
            print(f"Content length: {content['full_length']} characters")
            if content['truncated']:
                print("Note: Content was truncated for display")
            print(content['content'])

        # Read with custom limits
        full_content = get_library_content(
            filename="large_library.md",
            max_chars=50000  # Get more content
        )
    """
    try:
        filepath = os.path.join(base_dir, filename)

        if not os.path.exists(filepath):
            return {"error": f"File {filename} not found in {base_dir}"}

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Truncate if too long
        truncated = False
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... [Content truncated]"
            truncated = True

        return {
            "filename": filename,
            "content": content,
            "full_length": len(content),
            "truncated": truncated,
            "max_chars": max_chars,
        }

    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


def main() -> None:
    """Main entry point - supports both MCP server and CLI modes."""
    import sys

    # Check if running as CLI tool (has command line arguments)
    if len(sys.argv) > 1:
        # CLI mode - reuse the original argparse logic
        parser = argparse.ArgumentParser(
            description="Context7 Library Documentation Tool"
        )

        # Common arguments
        common_parser = argparse.ArgumentParser(add_help=False)
        common_parser.add_argument(
            "--client-ip", type=str, help="Optional client IP to send in headers"
        )

        subparsers = parser.add_subparsers(dest="command", required=True)

        # Search command
        search_parser = subparsers.add_parser(
            "search", help="Search for libraries", parents=[common_parser]
        )
        search_parser.add_argument("query", type=str, help="The search query")

        # Fetch command
        fetch_parser = subparsers.add_parser(
            "fetch",
            help="Fetch and save library documentation",
            parents=[common_parser],
        )
        fetch_parser.add_argument(
            "library_id",
            type=str,
            help="The ID of the library (e.g., /gradio-app/gradio)",
        )
        fetch_parser.add_argument(
            "--topic", type=str, help="Optional topic to focus on"
        )
        fetch_parser.add_argument(
            "--tokens", type=int, help="Optional max number of tokens"
        )
        fetch_parser.add_argument(
            "--output",
            type=str,
            help="File path to save the documentation. If not provided, saves to a default location.",
        )
        fetch_parser.add_argument(
            "--sync-repo",
            action="store_true",
            help="If enabled, automatically clone the GitHub repository if found in documentation",
        )
        fetch_parser.add_argument(
            "--search-query",
            type=str,
            help="Optional search query that was used to find this library (for INDEX.md tracking)",
        )

        args = parser.parse_args()

        if args.command == "search":
            # Use the internal implementation function for CLI
            client_ctx = {"clientIp": args.client_ip} if args.client_ip else None
            results = _search_libraries_impl(args.query, None, client_ctx)
            if results.get("error"):
                print(f"Error: {results['error']}")
            else:
                print(
                    results.get("formatted_text", results.get("message", "No results"))
                )
        elif args.command == "fetch":
            output_file = args.output
            if not output_file:
                # Default save location if --output is not provided
                sanitized_id = args.library_id.replace("/", "_").strip("_")
                output_file = f".kms/context7/km-base/{sanitized_id}.md"

            # Use the public wrapper which maps to v2 context API
            result = fetch_library_documentation(
                library_id=args.library_id,
                topic=args.topic,
                tokens=args.tokens,
                client_ip=args.client_ip,
                save_to_file=True,
                sync_repo=args.sync_repo,
                search_query=args.search_query,
            )

            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print("Documentation saved successfully:")
                if result.get("saved_to"):
                    print(f"  - File: {result['saved_to']}")
                if result.get("repo_cloned"):
                    print(f"  - Repository: {result['repo_cloned']}")
                elif result.get("repo_clone_failed"):
                    print(f"  - Repository clone failed: {result['repo_clone_failed']}")
                elif result.get("no_repo_found"):
                    print(f"  - {result['no_repo_found']}")
    else:
        # MCP server mode
        mcp.run()


if __name__ == "__main__":
    main()
