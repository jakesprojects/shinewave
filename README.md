# shinewave.io

> **Status:** 🪦 Archived / Discontinued  
> **Type:** Personal Project  
> **Domain:** Omnichannel Messaging, Sensitive Communications (e.g. Healthcare)

## Overview

**shinewave.io** was an experimental SaaS omnichannel messaging platform designed to enable complex, two-way communication in sensitive, high-stakes contexts such as healthcare, care coordination, and regulated customer interactions.

The project was an attempt to build a better configuration engine than the market currently serviced for messaging workflows. Human-in-the-loop messaging, and channel abstraction (SMS, email, in-app, etc.), and communication with arbitrary outside APIs could coexist in a single system while maintaining privacy, reliability, and auditability. Further, the goal was to provide a low-to-no-code solution for configuring these workflows, enabling customers to either handle their own configurations, or quickly-onboarded technicians to do the same, without the need for full-fledged scripting (as many existing solutions provide).

Ultimately, the project was abandoned for two reasons:
1. I got a job, and didn't have time to work on it.
2. With a limited moat around the technology (most aspects were unlikely to be patentable), the domain-shift would be relatively easy for existing CRM solutions (such as Braze), which could ultimately service this need better than a fledgling startup.

In short, the market opportunity didn't seem likely to supplant the income provided by a leadership role in an established data team in a reasonable timeframe. However, I've chosen to surface the work that went into this, since I don't have a portfolio of publicly-visible work. This project is also of particular interest, since minimal AI-assisted coding went into it (it was a different time). The vast majority of it (especially the Python/SQL/Infra work) was written solo. It was also a fun exploration of some novel technologies, including [NodeGraphQT](https://github.com/jchanvfx/NodeGraphQt) (Credit to [jchanvfx](https://github.com/jchanvfx)) and the [X Window System](https://en.wikipedia.org/wiki/X_Window_System) (something I had zero prior exposure to as a developer).

This repository is preserved for historical and educational purposes. Maybe it'll be useful to somebody. Note that it isn't in a production-ready state; this was a solo project, so versioned releases, solid branching/forking logic, and a complete CI/CD framework were never implemented.

---

## Repo Structure
- jakenode-master
  - This contains all of the logic for constructing a "Node Graph", which is essentially a DAG-builder that allows a user to structure messaging workflows.
- file_mount
  - This (poorly-named) folder contains the Flask Frontend (built from the [Flask Atlantis](https://app-generator.dev/product/atlantis-dark/flask/) template), as well as the "production" (not really) version of the "jakenode" app.
- shinewave_webapp
  - This contained all file-processing logic for the webapp
- NodeGraphQt-master
  - Just an archived copy of the NodeGraph app, so that I could run this locally and wouldn't get into trouble if it was ever deleted. In a clean repo, this would just be a fork.

---

## Problem Statement

> _Why this project existed_

- Sensitive industries (e.g., healthcare) require **two-way**, **context-aware**, and **auditable** messaging
- Existing tools were some combination of:
  - Not suited for sensitive domains (CRM tools are generally built around Marketing/Sales orgs, not direct outreach in a sensitive, operational context).
  - Hard to audit (no visual representation of workflows).
  - Poorly-designed for customer onboarding (limited self-service, complex configuration frameworks).
- Shinewave aimed to treat conversations as **stateful workflows**, not just message sends.

---

## Core Concepts

- **Omnichannel Messaging**
  - SMS, email, in-app, and extensible channel support
- **Two-Way Conversations**
  - Bidirectional, asynchronous communication
- **Conversation State**
  - Long-lived threads with context
- **Simple Setup**
  - Designed with ease-of-implementation as a top priority

---

## The Node App

Ultimately, messaging workflows were treated as [DAGs](https://en.wikipedia.org/wiki/Directed_acyclic_graph), which could be developed through a no-code, drag-and-drop interface. Said interface was designed to operate like existing collaborative tools; instead of restricting multiple users, or handling complex merge logic, multiple users could interface with a server hosting a workflow-building session simultaneously, and their adjustments would be reflected/visible in real time.

---

## Project State

What was completed:

* A working local prototype, with the multi-user, drag-and-drop app implemented.
* General skeletal outlines of how the various nodes would work (in Python).
* A file uploader, with basic file management, validation, and auditing as features.
* Mock data was generated for an analytics project, showcasing the kinds of reports that would be available upon completion.

What was not completed:

* Authentication. The mortal sin of hard-coding a login was committed ONLY because this was a prototype never meant for production
* The messaging scheduler
* The messaging executors, e.g. Twilio, email integration, etc.
* The full multi-tenant framework
* Cloud infrastructure
