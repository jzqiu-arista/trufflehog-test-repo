import os
import stat
import tarfile
import subprocess
import json

import requests

TRUFFLEHOG_VERSION = "3.63.7"
TRUFFLEHOG_ARCH = "arm64"
TRUFFLEHOG_PLATFORM = "linux"

TRUFFLEHOG_TAR_NAME = f"trufflehog_{TRUFFLEHOG_VERSION}_{TRUFFLEHOG_PLATFORM}_{TRUFFLEHOG_ARCH}.tar.gz"
TRUFFLEHOG_URL = f"https://github.com/trufflesecurity/trufflehog/releases/download/v{TRUFFLEHOG_VERSION}/{TRUFFLEHOG_TAR_NAME}"

response = requests.get(TRUFFLEHOG_URL, timeout=1000)
with open(TRUFFLEHOG_TAR_NAME, "wb") as file:
    file.write(response.content)

script_directory = os.path.dirname(os.path.abspath(__file__))
with tarfile.open(TRUFFLEHOG_TAR_NAME, "r:gz") as tar:
    tar.extractall(path=script_directory)

target = os.environ.get("GITHUB_WORKSPACE")
if not target:
    raise FileNotFoundError("$GITHUB_WORKSPACE not set in current environment")

binary_path = f"{script_directory}/trufflehog"
os.chmod(binary_path, stat.S_IEXEC)


scan_result = subprocess.run(
    [binary_path, "filesystem", "-j", "--fail", target],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)

secrets_found = []
for line in scan_result.stdout.split("\n"):
    if not line:
        continue
    secrets_found.append(json.loads(line))

if secrets_found:
    for s in secrets_found:
        print(f"[!] File Path: {s['SourceMetadata']['Data']['Filesystem']['file']}")
        print(f"[!] Raw Secret:\n{s['Raw']}")
        print()
    print(f"[!] Found {len(secrets_found)} secrets. Please remove them from the repository and rotate them ASAP.")
    exit(1)
else:
    print("[+] No secrets found. You are good to go!")
    