# Pico Runtime Figma Capture Design

**Goal:** Replace the dense Excalidraw-only architecture view with a cleaner, presentation-grade Figma design generated from a local HTML/CSS slide deck.

**Audience**

Developers who need to understand what happens on the Pico without reading code-level variable names. The content should explain behavior in plain English and emphasize the runtime story over implementation identifiers.

**Scope**

The revised design keeps the same Pico-local scope:

- physical inputs and local peripherals
- the real-time sampling loop
- per-channel tracking and dip detection behavior
- optional offloaded work for display and storage
- local runtime modes and outputs

It removes code-ish labels and avoids exposing internal variable names unless absolutely necessary.

**Selected Approach**

Use a local HTML/CSS artifact as the source of truth, then capture it into a new Figma design file using the Figma MCP capture workflow.

The page will contain three slide-style sections:

1. Overview
2. Sampling and dip detection
3. Local outputs and runtime modes

This approach is preferred over continuing in Excalidraw because the user explicitly wants cleaner spacing, no clipping, and stronger presentation quality.

**Content Rules**

- explain what each part does, not what a variable is called
- keep text inside containers and avoid long paragraphs in tight boxes
- use fewer, larger regions with stronger whitespace
- prefer 2-3 visual groups per slide instead of one overloaded canvas

**Visual Direction**

- light background with strong structure and consistent spacing
- large slide cards with clear headings and short explanatory copy
- timing badges such as `10 ms`, `100 ms`, `60 s`, and `600 s`
- color coding for input, processing, detection, and output concerns
- no monolithic side rail full of settings

**Slide Breakdown**

**Slide 1: Overview**
- physical signals enter the Pico
- the Pico samples every 10 ms
- each channel keeps its own idea of what normal looks like
- optional secondary worker handles slower display and storage tasks
- local outputs remain on-device

**Slide 2: Sampling and dip detection**
- raw readings are checked for signal quality
- the monitor learns a stable baseline
- short voltage drops trigger dip start and dip end events
- hysteresis and cooldown prevent noisy retriggering
- median snapshots happen at a slower cadence than raw detection

**Slide 3: Local outputs and modes**
- display-only mode prioritizes smooth on-device visuals
- event-only mode stores important events with low flash wear
- full local mode stores ongoing median history on-device
- OLED, flash writes, and status reporting are local consumers of the same sensing pipeline

**Validation**

The deliverable is complete only after:

- the local HTML renders cleanly in a browser
- the page is captured into a new Figma design file
- the capture completes successfully
- the resulting Figma file is shared back to the user
