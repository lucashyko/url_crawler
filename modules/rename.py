import json
from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    """Normalize a URL by removing the trailing slash."""
    parsed_url = urlparse(url)
    # Reconstruct the URL without a trailing slash
    normalized_url = parsed_url._replace(path=parsed_url.path.rstrip('/')).geturl()
    return normalized_url

def filter_duplicate_urls(urls: list) -> list:
    """Filter out duplicate URLs that only differ by a trailing slash."""
    seen = set()
    unique_urls = []
    for url in urls:
        normalized_url = normalize_url(url)
        if normalized_url not in seen:
            seen.add(normalized_url)
            unique_urls.append(url)  # Keep the original URL (with or without trailing slash)
    return unique_urls

def load_urls(file_path: str) -> list:
    """Load URLs from a JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("urls", [])
    except Exception as e:
        print(f"Failed to load URLs from {file_path}: {str(e)}")
        raise

def save_urls(file_path: str, urls: list):
    """Save URLs to a JSON file."""
    try:
        with open(file_path, "w") as file:
            json.dump({"urls": urls}, file, indent=4)
        print(f"Cleaned URLs saved to {file_path}")
    except Exception as e:
        print(f"Failed to save URLs to {file_path}: {str(e)}")
        raise

def clean_urls(file_path: str):
    """Clean the URLs in the specified JSON file."""
    # Load URLs
    urls = load_urls(file_path)
    print(f"Loaded {len(urls)} URLs from {file_path}")

    # Filter duplicates
    unique_urls = filter_duplicate_urls(urls)
    print(f"Found {len(urls) - len(unique_urls)} duplicates.")

    # Save cleaned URLs
    save_urls(file_path, unique_urls)
    print(f"Saved {len(unique_urls)} unique URLs to {file_path}")

if __name__ == "__main__":
    # Path to the URLs file
    urls_file = "urls.json"

    # Clean the URLs
    clean_urls(urls_file)