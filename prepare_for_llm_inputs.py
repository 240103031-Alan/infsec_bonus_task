import os
import json
import re
import subprocess
from pathlib import Path

OUTPUT_DIR = "output"
LLM_DIR = "llm_input"
REPOS_DIR = "repos"

# ----------------------------
# Extract changed files from diff
# ----------------------------
def extract_changed_files(diff_text):
    changed = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            fname = line.replace("+++ b/", "").strip()
            changed.append(fname)
    return changed


# ----------------------------
# Read file from repo at specific commit
# ----------------------------
def get_file_at_commit(repo_path, commit_hash, filename):
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "show", f"{commit_hash}:{filename}"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except:
        return None


# ----------------------------
# Main processing
# ----------------------------
def main():
    Path(LLM_DIR).mkdir(exist_ok=True)
    
    for ghsa_folder in os.listdir(OUTPUT_DIR):
        adv_path = os.path.join(OUTPUT_DIR, ghsa_folder)
        if not os.path.isdir(adv_path):
            continue

        repo_path = os.path.join(REPOS_DIR, ghsa_folder)
        if not os.path.exists(repo_path):
            print(f"[WARN] No repo for {ghsa_folder}, skipping.")
            continue

        print(f"\n==== Processing advisory {ghsa_folder} ====")

        for fname in os.listdir(adv_path):
            if not fname.endswith(".diff"):
                continue

            commit_hash = fname.replace(".diff", "")
            diff_file = os.path.join(adv_path, fname)

            print(f"[INFO] Processing commit {commit_hash}")

            # Read diff text
            diff_text = open(diff_file, "r", encoding="utf-8").read()

            # Get changed files
            changed_files = extract_changed_files(diff_text)

            # Prepare LLM folder
            commit_dir = os.path.join(LLM_DIR, ghsa_folder, commit_hash)
            old_dir = os.path.join(commit_dir, "old")
            new_dir = os.path.join(commit_dir, "new")

            Path(commit_dir).mkdir(parents=True, exist_ok=True)
            Path(old_dir).mkdir(exist_ok=True)
            Path(new_dir).mkdir(exist_ok=True)

            # Save patch
            with open(os.path.join(commit_dir, "patch.diff"), "w", encoding="utf-8") as f:
                f.write(diff_text)

            results = {"changed_files": changed_files, "files_saved": []}

            # Save old/new versions
            for fpath in changed_files:
                print(f"   → Extracting {fpath}")

                old_code = get_file_at_commit(repo_path, f"{commit_hash}~1", fpath)
                new_code = get_file_at_commit(repo_path, commit_hash, fpath)

                record = {"file": fpath, "old": False, "new": False}

                if old_code:
                    out = os.path.join(old_dir, fpath.replace("/", "_"))
                    with open(out, "w", encoding="utf-8") as f:
                        f.write(old_code)
                    record["old"] = True

                if new_code:
                    out = os.path.join(new_dir, fpath.replace("/", "_"))
                    with open(out, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    record["new"] = True

                results["files_saved"].append(record)

            # Save summary
            with open(os.path.join(commit_dir, "summary.json"), "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

            print(f"[DONE] Created LLM package for commit {commit_hash}")

    print("\n[ALL COMPLETE] You can now feed llm_input/* folders to your LLM.")


if __name__ == "__main__":
    main()
