# shinewave.io

> **Status:** Archived / Discontinued  
> **Type:** Personal Project (Solo)  
> **Domain:** Omnichannel Messaging, Sensitive & Regulated Communications

---

## Overview

**shinewave.io** was an experimental SaaS platform for configuring and managing **stateful, two-way messaging workflows** in sensitive, high-stakes contexts such as healthcare, care coordination, and regulated customer communications.

The system focused on modeling conversations as **explicit workflows** with validation, persistence, and auditability, rather than treating messages as isolated delivery events. The workflow editor was implemented as a [Directed Acyclic Graph (DAG)](https://en.wikipedia.org/wiki/Directed_acyclic_graph) builder, allowing non-engineers to configure complex logic visually.

A central technical component of the project was a custom node-graph system built on top of (NodeGraphQt)[https://github.com/jchanvfx/NodeGraphQt], extended to support domain-specific validation, persistence, and multi-user interaction. Portions of the UI experimentation also involved working directly with the [X Window System](https://en.wikipedia.org/wiki/X_Window_System) to better understand lower-level windowing behavior.

At its core, shinewave emphasized **workflow structure, correctness, and visibility**, rather than channel execution or growth tooling.

---

## How to Read This Repository

This repository contains a mix of core architectural work, prototype‑level implementations, and exploratory code typical of an early‑stage system.

Readers primarily interested in **system design and engineering tradeoffs** may find the following areas most relevant:

- **Graph persistence & validation**  
  `jakenode/graph_handler.py`  
  Custom graph serialization, validation, versioning, and database‑backed persistence for DAG‑based workflows.

- **Node system & domain modeling**  
  `jakenode/nodes/`  
  Trigger, outreach, and workflow‑change nodes with domain‑specific constraints and validation logic.

- **Workflow validation & UX feedback**  
  Graph‑level and node‑level validation with aggregated, user‑friendly error reporting.

- **File ingestion & validation**  
  CSV ingestion with schema normalization, aliasing, partial‑row validation, and audit‑friendly handling of imperfect data.

Other areas reflect supporting or exploratory work and are preserved primarily for context.

---

## Problem Context

Sensitive industries (e.g. healthcare, care coordination, regulated services) impose requirements that many existing messaging tools handle poorly:

- **Two‑way, asynchronous conversations** rather than one‑off sends
- **Context and state** that persist across time
- **Auditability and traceability** of workflow behavior
- **Safe onboarding and configuration** without requiring full scripting

Shinewave treated conversations as **explicit state machines**, not just delivery events, and aimed to make those workflows visible, inspectable, and configurable.

---

## Core Concepts

- **Omnichannel Messaging**  
  Abstracted support for SMS, email, in‑app messaging, and extensible channels

- **Two‑Way Conversations**  
  Bidirectional, asynchronous communication modeled as workflows

- **Conversation State**  
  Long‑lived threads with explicit transitions and validation

- **Low‑Code Configuration**  
  Drag‑and‑drop workflow construction rather than scripting‑heavy configuration

---

## The Node Graph System

Messaging workflows were modeled as **Directed Acyclic Graphs (DAGs)** and constructed through a no‑code, drag‑and‑drop interface.

Key characteristics:

- Multi‑user, real‑time graph editing
- Domain‑specific node types (triggers, outreach, workflow transitions)
- Graph‑level and node‑level validation
- Explicit persistence and versioning of workflow definitions

Rather than restricting concurrent editing or implementing complex merge semantics, multiple users could interact with a shared session simultaneously, with changes reflected in real time.

---

## Project State

### What Was Implemented

- A working local prototype with a multi‑user, drag‑and‑drop workflow editor
- Custom graph persistence, validation, and versioning logic
- A domain‑modeled node system with enforceable constraints
- File upload, validation, and basic auditing functionality
- Mock analytics data illustrating intended reporting surfaces

### Out of Scope for This Prototype

The following areas were intentionally deferred to keep the project focused on workflow modeling and system architecture:

- Authentication and authorization
- Production messaging executors (e.g. SMS/email providers)
- Messaging schedulers
- Full multi‑tenant isolation
- Cloud infrastructure and CI/CD

---

## Repository Structure

- **jakenode‑master**  
  Core node‑graph system: graph construction, validation, persistence, and node definitions.

- **file_mount**  
  Flask‑based frontend (derived from a template) and a locally runnable version of the node editor.

- **shinewave_webapp**  
  File ingestion, validation, and supporting backend logic.

- **NodeGraphQt‑master**  
  Archived copy of NodeGraphQt for local execution. In a clean production repository, this would be maintained as a fork.

---

## Why the Project Was Archived

This project was started independently and progressed to a working prototype, but was never completed as a production product.

Completing it would have required a long-term commitment to productization, operations, and go-to-market work in a domain where the opportunity cost did not justify continued investment once I returned to a full-time leadership role.

At that point, I chose to stop further development and preserve the work as-is. The repository reflects an unfinished system that reached a natural stopping point based on prioritization, not ambiguity about the technical direction.

---

## Notes

This repository is preserved for historical and educational purposes. It reflects an end‑to‑end, solo‑built prototype with an emphasis on **explicit state management, validation, and persistence**, rather than on framework‑heavy abstraction or production hardening.

Screenshots below illustrate the intended user experience and system surfaces.

---

## Application Screenshots

### Webapp
<img width="800" height="447" alt="shinewave" src="https://github.com/user-attachments/assets/d173ae19-31d2-4b35-91e4-643c00a2cbbe" />

### Workflow Details
<img width="960" height="540" alt="Workflow View" src="https://github.com/user-attachments/assets/8650356e-c4b2-497b-a443-af4d5e9578fe" />
<img width="960" height="540" alt="Workflow Details" src="https://github.com/user-attachments/assets/75d4cc82-1bd8-4baa-98ae-18b7f9edf975" />

### Analytics
<img width="960" height="540" alt="Analytics View" src="https://github.com/user-attachments/assets/476174eb-e57b-4d46-b394-5be2fd0412d9" />
<img width="960" height="540" alt="Analytics View" src="https://github.com/user-attachments/assets/7a1026e5-2304-4eb2-9dc9-d53c174e4f31" />
<img width="960" height="540" alt="Analytics View" src="https://github.com/user-attachments/assets/a9af8a03-1893-49df-b708-bb7e6e452b5e" />
