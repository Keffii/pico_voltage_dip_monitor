# Pico Runtime Figma Capture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a clean three-slide Pico runtime explanation page locally and capture it into a new Figma design file.

**Architecture:** Create a static HTML/CSS page under `docs/diagrams` so the diagram can be controlled precisely for spacing, wrapping, and visual hierarchy. Serve it on localhost, then use the Figma MCP capture workflow to generate a new Figma design file in the user's team.

**Tech Stack:** HTML, CSS, Python `http.server`, Figma MCP capture workflow

---

### Task 1: Create the local slide deck source

**Files:**
- Create: `docs/diagrams/pico-runtime-figma/index.html`

**Step 1: Define the three-slide structure**

Create sections for:
- overview
- sampling and dip detection
- local outputs and modes

**Step 2: Replace variable names with behavior-focused language**

Use labels such as:
- `Learns what stable voltage looks like`
- `Checks whether a drop is real or just noise`
- `Moves slower display and storage work off the critical path`

**Step 3: Build large, spaced containers**

Use CSS grid/flex layouts and fixed-width cards so text wraps safely inside each region.

### Task 2: Verify the local page visually

**Files:**
- Verify: `docs/diagrams/pico-runtime-figma/index.html`

**Step 1: Open via local server**

Serve the page from localhost.

**Step 2: Check layout manually**

Confirm:
- no text overflow
- strong whitespace between regions
- readable hierarchy
- slide-level separation

### Task 3: Capture into Figma

**Files:**
- Generate: new Figma design file

**Step 1: Start the local server**

Run a localhost server rooted at the diagram directory.

**Step 2: Use `generate_figma_design` in `newFile` mode**

Capture the local page into a new design file under the available team plan.

**Step 3: Poll until complete**

Wait for completion and record the returned file information.

### Task 4: Verify completion and hand off

**Files:**
- Reference: `docs/plans/2026-03-11-pico-runtime-figma-capture-design.md`
- Reference: `docs/plans/2026-03-11-pico-runtime-figma-capture.md`

**Step 1: Confirm artifact paths**

Report the local HTML source path and the resulting Figma file details.

**Step 2: Call out limitations**

If the capture tool changes frame naming or layout slightly, note that the local HTML remains the editable source of truth.
