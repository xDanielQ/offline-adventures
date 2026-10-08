---
title: "Offline Adventures: A Local AI Nudge to Get Off the Screen"
published: false
tags: devchallenge, hf26challenge, opensource, localai
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

Offline Adventures is a local-first activity recommender designed to make choosing an activity quick, then get out of the way.

The user selects available time, energy level, current weather, accessible places, group type, and interests. The app returns one primary adventure and two alternatives. Each recommendation includes a short explanation, a mission, practical notes, a memory prompt, and a personalized local-AI twist.

The catalog covers walking, running, cycling, photography, nature, public art, local history, gardening, games, reading outdoors, family activities, sheltered activities, and indoor activities that prepare the next trip outside.

The interface is available through Streamlit on the local network, so I can open the recommendation on a phone and take the mission outside without carrying a laptop.

## Demo

**Demo video:** `<DEMO_VIDEO_URL>`

Tested scenarios:

1. **Dry weather, low energy, photography and nature**
   - Produces an outdoor recommendation and two alternatives.
   - Repeated clicks rotate through unseen matching activities.

2. **Heavy rain, family, games and nature**
   - Produces sheltered or indoor-bridge options instead of unsuitable outdoor recommendations.

3. **Restrictive conditions**
   - The app explains when fewer than three activities match instead of inventing unsafe or incompatible options.

## Code

**Repository:** `https://github.com/xDanielQ/offline-adventures`

The repository includes the curated 50-activity catalog, automated tests, a catalog validator, and a real Ollama smoke test.

## How I Built It

The application uses a deliberately hybrid architecture.

Deterministic Python code handles hard constraints:

- available time;
- energy level;
- current weather;
- accessible place types;
- group type;
- candidate ID validation;
- session diversity.

After filtering, up to 15 approved candidates are sent to a local `llama3.1:8b-instruct-q4_K_M` model through Ollama. The model performs semantic ranking, selects one primary activity and two alternatives, writes a natural explanation, and generates a small `personalized_twist` for each choice.

Pydantic generates the response schema and validates the structured JSON returned by Ollama. The model is not allowed to invent activity IDs. It also receives explicit boundaries against inventing locations, equipment, health advice, risky behavior, or laptop use during the activity.

The final flow is:

```text
Streamlit input
→ deterministic constraints
→ varied approved candidate pool
→ local open-weight model
→ Pydantic-validated structured result
→ short mission for the real world
```

I first tested using the model to generate the whole catalog. The records were structurally valid, but the content was repetitive, overused a "find, photograph, research" pattern, and did not provide the desired activity distribution. That experiment changed the architecture: people curate the activity catalog, Python enforces hard rules, and the model handles semantic choice and personalization.

The tested system used:

- NVIDIA RTX 2060 SUPER with 8 GB VRAM;
- 24 GB system RAM;
- Intel i5-7600K;
- Python 3.12;
- Streamlit;
- Ollama;
- `llama3.1:8b-instruct-q4_K_M`.

At submission time the project had 19 passing tests and a validated catalog distribution of 30 outdoor, 8 sheltered, and 12 indoor-bridge activities.

## Why Does Open Innovation Matter?

Local open-weight AI is important here for practical reasons, not just ideology.

The user's interests, available places, group context, and weather remain on the user's machine. The app does not need a hosted AI key, an account, or a per-request fee. The model can be replaced or its prompt and behavior can be inspected and changed. The project can continue to work in a local network even without an external AI service.

A closed API could generate similar text, but it would add a remote dependency to an application specifically designed to shorten screen time and keep everyday context private. Local inference makes the architecture match the product goal.

Open tooling also made the failures visible. I could inspect candidate lists, validate every output with Pydantic, compare model-generated catalog content with curated content, and keep deterministic rules outside the model.

## My Agent Session

`{% agent_session <DEVRELAY_SESSION_ID_OR_SLUG> %}`

The session documents the design decisions, catalog experiment, structured-output validation, local-model integration, and the choice to keep safety constraints deterministic.

## Prize Categories

I am entering the overall Hacktoberfest Open-Source AI Challenge: Week 1, Touch Grass category.


