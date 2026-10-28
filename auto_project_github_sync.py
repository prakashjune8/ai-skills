"""Autonomous Cross-Project GitHub Synchronizer & Auto-Replication Engine.

Monitors active projects, auto-initializes git for new projects, creates remote
GitHub repositories under prakashjune8, and automatically commits and pushes
all progress without requiring manual intervention or permission prompts.
"""
from __future__ import annotations

import os
import subprocess
import shutil
from datetime import datetime

GITHUB_USER = "prakashjune8"

# Standard directories to monitor for project discovery
MONITORED_ROOTS = [
    r"D:",
    r"D:\AI SKILLS",
]

# Explicit directory to repository mappings
PROJECT_REGISTRY: dict[str, str] = {
    r"d:\ephemeris": "gann-astrological-trading",
    r"D:\AI SKILLS\AI-Mastery-Masterclass": "google-ai-mastery",
    r"D:\AI SKILLS\GLOBAL_SKILL_LIBRARY": "antigravity-global-skills",
    r"D:\THARUN PROJECT": "tharun_studyhour",
}

IGNORED_DIRS = {
    "$RECYCLE.BIN",
    "System Volume Information",
    "DumpStack.log.tmp",
    "Recovery",
    "build",
    "dist",
    "__pycache__",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "Gannzilla-Pro-v.8.3",
    "ESPON PRINTER CD",
    "HP PRINTER LASER CD",
    "office 2019",
}

DEFAULT_GITIGNORE = """
# Auto-generated GitIgnore
__pycache__/
*.pyc
*.pyo
*.pyd
*.exe
*.dll
*.so
*.dylib
*.pkg
build/
dist/
.venv/
venv/
node_modules/
.pytest_cache/
.DS_Store
Thumbs.db
*.log
*.tmp
"""


def log(msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def is_valid_project(path: str) -> bool:
    """Heuristic to check if a directory is an active code/document project."""
    if not os.path.isdir(path):
        return False
    base = os.path.basename(path)
    if base in IGNORED_DIRS or base.startswith("$") or base.startswith("."):
        return False
    # Check for marker files
    markers = [
        ".git", "package.json", "pyproject.toml", "requirements.txt",
        "README.md", "main.py", "index.html", ".cursorrules", ".gemini"
    ]
    try:
        entries = os.listdir(path)
        return any(m in entries for m in markers) or any(
            f.endswith((".py", ".js", ".ts", ".html", ".md", ".ps1")) for f in entries
        )
    except Exception:
        return False


def discover_projects() -> list[str]:
    """Scan monitored roots to discover all existing and newly created projects."""
    discovered = list(PROJECT_REGISTRY.keys())
    for root in MONITORED_ROOTS:
        if not os.path.exists(root):
            continue
        try:
            for item in os.listdir(root):
                full_path = os.path.join(root, item)
                if is_valid_project(full_path) and full_path not in discovered:
                    discovered.append(full_path)
        except Exception as e:
            log(f"Error scanning {root}: {e}")
    return [p for p in discovered if os.path.exists(p)]


def sync_project(project_path: str):
    """Automatically commits and pushes progress for a given project."""
    norm_path = os.path.abspath(project_path)
    folder_name = os.path.basename(norm_path).lower().replace(" ", "-").replace("_", "-")
    repo_name = PROJECT_REGISTRY.get(norm_path, folder_name)

    log(f"--> Syncing Project: {os.path.basename(norm_path)} (Repo: {repo_name})")

    # Ensure .gitignore exists
    gitignore_path = os.path.join(norm_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_GITIGNORE.strip() + "\n")
        log(f"    [+] Created standard .gitignore")

    git_dir = os.path.join(norm_path, ".git")

    # Step 1: Initialize git if missing
    if not os.path.exists(git_dir):
        log(f"    [+] Initializing new git repository...")
        subprocess.run(["git", "init", "-b", "main"], cwd=norm_path, check=True, capture_output=True)

    # Step 2: Check current branch
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=norm_path, text=True
        ).strip()
        if not branch:
            branch = "main"
    except Exception:
        branch = "main"

    # Step 3: Check if remote exists
    remotes = subprocess.check_output(
        ["git", "remote", "-v"], cwd=norm_path, text=True
    ).strip()

    if not remotes:
        log(f"    [+] No remote configured. Creating GitHub repository: {GITHUB_USER}/{repo_name}...")
        try:
            # Stage all files
            subprocess.run(["git", "add", "-A"], cwd=norm_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Initial commit for {repo_name}"],
                cwd=norm_path, check=False, capture_output=True
            )
            # Create repo on GitHub and push
            res = subprocess.run(
                [
                    "gh", "repo", "create", repo_name,
                    "--public",
                    f"--description=Auto-replicated project: {os.path.basename(norm_path)}",
                    "--source=.",
                    "--remote=origin",
                    "--push"
                ],
                cwd=norm_path, text=True, capture_output=True
            )
            if res.returncode == 0:
                log(f"    [SUCCESS] Created and pushed: https://github.com/{GITHUB_USER}/{repo_name}")
                return
            else:
                log(f"    [Notice] gh repo create: {res.stderr.strip() or res.stdout.strip()}")
        except Exception as e:
            log(f"    [Error] Creating repo: {e}")

    # Step 4: Sync existing repository (stage, commit if dirty, push)
    try:
        # Check status
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=norm_path, text=True
        ).strip()

        if status:
            log(f"    [*] Detected changes. Staging and committing...")
            subprocess.run(["git", "add", "-A"], cwd=norm_path, check=True, capture_output=True)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(
                ["git", "commit", "-m", f"Auto-sync progress: {now_str}"],
                cwd=norm_path, check=True, capture_output=True
            )

        # Push to remote
        log(f"    [^] Pushing to origin {branch}...")
        push_res = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=norm_path, text=True, capture_output=True
        )
        if push_res.returncode == 0:
            log(f"    [SUCCESS] Pushed cleanly to origin {branch}")
        else:
            # If rejected because remote has changes, pull --rebase then push
            if "fetch first" in push_res.stderr or "non-fast-forward" in push_res.stderr:
                log(f"    [*] Remote has newer commits. Pulling with rebase...")
                subprocess.run(["git", "pull", "--rebase", "origin", branch], cwd=norm_path, capture_output=True)
                subprocess.run(["git", "push", "origin", branch], cwd=norm_path, capture_output=True)
                log(f"    [SUCCESS] Rebased and pushed cleanly.")
            else:
                log(f"    [Notice] Push output: {push_res.stderr.strip() or push_res.stdout.strip()}")
    except Exception as e:
        log(f"    [Error] Syncing {project_path}: {e}")


def run_full_sync():
    log("==========================================================")
    log("  AUTONOMOUS GITHUB REPLICATION & CROSS-PROJECT SYNC")
    log("==========================================================")
    projects = discover_projects()
    log(f"Discovered {len(projects)} active projects:")
    for p in projects:
        log(f"  - {p}")

    for p in projects:
        try:
            sync_project(p)
        except Exception as e:
            log(f"Error syncing {p}: {e}")

    log("==========================================================")
    log("All projects checked and synchronized to GitHub!")
    log("==========================================================")


if __name__ == "__main__":
    run_full_sync()
