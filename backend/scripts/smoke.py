"""Simple real-model smoke CLI. Requires healthy API and token in environment."""
import os
import sys
import urllib.request


def main():
    base = os.environ.get("API_URL", "http://127.0.0.1:8006")
    for path in ("/health/live", "/health/ready"):
        with urllib.request.urlopen(base + path, timeout=10) as response:
            print(path, response.status, response.read().decode())
    if len(sys.argv) > 1:
        import uuid
        path = sys.argv[1]
        content = open(path, "rb").read()
        boundary = "superapp" + uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"sample.png\"\r\n"
                "Content-Type: image/png\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(base + "/v1/detect", data=body, headers={
            "X-API-Key": os.environ.get("API_TOKEN", ""),
            "Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(request, timeout=180) as response:
            print(response.read().decode())


if __name__ == "__main__":
    main()
