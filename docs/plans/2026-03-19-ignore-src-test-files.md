# Ignore `src/test_*.py` Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `src/test_*.py` ignored and untracked by Git so those files stop being committed and pushed by default.

**Architecture:** Keep the change limited to Git metadata and repo policy by editing `.gitignore` and removing the existing `src/test_*.py` files from the index with `git rm --cached`. Perform the work in an isolated worktree because the main worktree already contains unrelated local changes.

**Tech Stack:** Git, `.gitignore`, repository-local Python files under `src/`

---

### Task 1: Define the ignore policy in `.gitignore`

**Files:**
- Modify: `.gitignore`

**Step 1: Add the ignore rule**

Append a narrow rule to `.gitignore`:

```gitignore
src/test_*.py
```

**Step 2: Verify the file diff**

Run: `git diff -- .gitignore`
Expected: only the new `src/test_*.py` ignore rule is added.

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore src test scripts"
```

### Task 2: Remove currently tracked `src/test_*.py` files from the index

**Files:**
- Update index only: `src/test_*.py`

**Step 1: Remove the tracked test scripts from the index without deleting local files**

Run:

```bash
git rm --cached src/test_*.py
```

Expected: Git schedules the tracked `src/test_*.py` files for deletion from the repository index while leaving them in the working tree.

**Step 2: Verify the files still exist locally**

Run: `Get-ChildItem src -Filter test_*.py`
Expected: the files are still present on disk.

**Step 3: Verify Git no longer tracks them**

Run: `git ls-files src/test_*.py`
Expected: no output.

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: stop tracking src test scripts"
```

### Task 3: Verify final repository state and integrate

**Files:**
- Verify: `.gitignore`
- Verify: `src/test_*.py`

**Step 1: Verify status**

Run: `git status --short`
Expected: no unexpected tracked changes from this task remain in the isolated worktree.

**Step 2: Verify ignore behavior**

Run: `git check-ignore src/test_ui_button_toggle.py`
Expected: Git reports that the file is ignored by the new rule.

**Step 3: Merge or fast-forward the isolated branch back to `main`**

Run the normal local integration path after confirming the worktree is clean.

**Step 4: Push**

Run: `git push`
Expected: remote `main` updates with the `.gitignore` and index policy change.
