# Ignore `src/test_*.py` Design

**Goal:** Stop tracking and committing `src/test_*.py` files by default, while keeping the files available locally in the workspace.

**Context**

The repository currently tracks all `src/test_*.py` files, and the existing `.gitignore` does not exclude them. Adding a new ignore rule alone would only affect future untracked files; it would not stop Git from continuing to track the test files that are already in the index.

The requested outcome is stricter: the `src/test_*.py` files should stop being committed and pushed unless they are explicitly force-added later.

**Approach**

Use a two-part Git policy change:

- Add `src/test_*.py` to `.gitignore` so future test scripts under `src/` are ignored by default.
- Remove the currently tracked `src/test_*.py` files from the Git index with `git rm --cached` so Git stops tracking them, while leaving the files on disk.

Apply this change in an isolated worktree because the main worktree already has unrelated local modifications.

**Why This Approach**

- It matches the requested behavior: the files remain locally available but stop participating in normal commits.
- It avoids deleting any local test files.
- It keeps the ignore scope narrow to `src/test_*.py`, which is what you requested.
- It avoids touching unrelated tracked files or broader test patterns elsewhere in the repo.

**Behavior Details**

- Existing `src/test_*.py` files stay on disk after the change.
- Git stops tracking those files after they are removed from the index.
- Future edits to those files no longer appear in normal `git status` output.
- New `src/test_*.py` files also stay ignored by default.
- If one of those files ever needs to be committed intentionally, it can still be added explicitly with force.

**Verification**

After the change:

- `.gitignore` contains `src/test_*.py`
- `git ls-files src/test_*.py` returns no tracked matches
- `git status --short` no longer lists the `src/test_*.py` files as tracked content
- the resulting commit can be pushed without disturbing unrelated local changes
