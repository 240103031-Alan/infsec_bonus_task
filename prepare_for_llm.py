import os
import json
import subprocess
import re
from pathlib import Path

# -------------------------------
# 1. Load parsed advisories
# -------------------------------

INPUT_JSON = "advisories.json"
OUTPUT_DIR = "output"


def load_advisories():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# 2. Clone repo if not exists
# -------------------------------

def clone_repo(repo_url, dst_path):
    if os.path.exists(dst_path):
        print(f"[INFO] Repo already exists: {dst_path}")
        return
    
    print(f"[INFO] Cloning repo: {repo_url}")
    subprocess.run(["git", "clone", repo_url, dst_path], check=True)


# -------------------------------
# 3. Extract commit hash from references
# -------------------------------

def extract_commit_hashes(references):
    commit_hashes = []

    for ref in references:
        match = re.search(r"/commit/([0-9a-f]{7,40})", ref)
        if match:
            commit_hashes.append(match.group(1))

    return commit_hashes


# -------------------------------
# 4. Run git show and save diff
# -------------------------------

def get_commit_diff(repo_path, commit_hash):
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "show", commit_hash],
            capture_output=True, text=True
        )
        return result.stdout
    except Exception as e:
        print("[ERROR] git show failed:", e)
        return ""


# -------------------------------
# 5. Parse diff to extract changed files + functions
# -------------------------------

def parse_diff(diff_text):
    changed_files = []
    changed_functions = []

    for line in diff_text.splitlines():
        # Detect changed files
        if line.startswith("+++ b/"):
            filename = line.replace("+++ b/", "").strip()
            changed_files.append(filename)

        # Function detection (Python, JS, etc.)
        if re.match(r"^\s*(def|class)\s+\w+", line):
            func = line.strip()
            changed_functions.append(func)

    return changed_files, changed_functions


# -------------------------------
# 6. Process all advisories
# -------------------------------

def process_all():
    advisories = load_advisories()
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    for adv in advisories:
        ghsa = adv["ghsa_id"]
        repo_url = adv["source_code_location"]
        references = adv["references"]

        print("\n==============================")
        print(f"Processing {ghsa}")
        print("==============================")

        # repo path
        repo_path = f"repos/{ghsa}"
        Path(repo_path).parent.mkdir(exist_ok=True)

        # clone repo
        clone_repo(repo_url, repo_path)

        # extract commit hashes
        commit_hashes = extract_commit_hashes(references)

        # create folder for output
        adv_out_dir = f"{OUTPUT_DIR}/{ghsa}"
        Path(adv_out_dir).mkdir(exist_ok=True)

        for commit in commit_hashes:
            print(f"[INFO] Extracting commit: {commit}")

            diff_text = get_commit_diff(repo_path, commit)

            diff_path = f"{adv_out_dir}/{commit}.diff"
            with open(diff_path, "w", encoding="utf-8") as f:
                f.write(diff_text)

            changed_files, changed_functions = parse_diff(diff_text)

            # save files
            with open(f"{adv_out_dir}/{commit}_files.json", "w", encoding="utf-8") as f:
                json.dump(changed_files, f, indent=2)

            with open(f"{adv_out_dir}/{commit}_functions.json", "w", encoding="utf-8") as f:
                json.dump(changed_functions, f, indent=2)

            print(f"[INFO] Saved diff + metadata for commit {commit}")

    print("\n[ALL DONE] You can now feed .diff or .json files to your LLM.")


# -------------------------------
# Run
# -------------------------------

if __name__ == "__main__":
    process_all()
