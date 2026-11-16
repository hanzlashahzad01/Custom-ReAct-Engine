# Custom ReAct Engine (Reason + Act + Observe + Reflect)

A modular, lightweight, and extensible **ReAct (Reasoning + Acting) Agent Engine** with **Reflection & Error Recovery** built in Python.

---

## 📌 Project Overview

Traditional LLM workflows often rely on standard prompt-completion or pure Chain-of-Thought (CoT). While CoT reasons step-by-step, it lacks the ability to interact with real-world environments, verify facts dynamically, or recover from errors.

The **ReAct (Reasoning + Acting)** framework synergizes reasoning traces and task-specific actions. This project implements a custom ReAct Engine augmented with an explicit **Reflection & Self-Correction Loop**:

1. **Reason (Thought):** Understand user intent, analyze constraints, and determine the next action.
2. **Act (Action):** Invoke tools (e.g., Safe AST Calculator or REST Countries API).
3. **Observe (Observation):** Collect raw execution outputs, status codes, or errors.
4. **Reflect (Reflection):** Evaluate whether the observation is valid, complete, and answers the query. If an error is detected, formulate a critique and suggest corrective actions (retry with alternative parameters or fallback).
5. **Final Answer:** Synthesize the verified result into a clean, human-readable response.

---

## 🏗️ Architecture & Workflow

```mermaid
flowchart TD
    Start([User Input]) --> Reason[1. Reason / Thought]
    Reason --> Act[2. Act / Tool Selection]
    Act --> Tools{Tool Registry}
    Tools -->|Math Expression| Calc[Calculator Tool]
    Tools -->|Country Info| API[Country API Tool]
    Calc --> Observe[3. Observe / Capture Result]
    API --> Observe
    Observe --> Reflect[4. Reflect / Error Analysis]
    Reflect -->|Error Detected / Retry Needed| Recovery[Error Recovery Strategy]
    Recovery -->|Adjusted Thought & Parameters| Reason
    Reflect -->|Valid & Sound| FinalAnswer([5. Final Answer])
```

---

## 📂 Project Structure

```text
Custom-ReAct-Engine/
│
├── main.py              # CLI entry point, menu, and automated test runners
├── tools.py             # Calculator (AST safe evaluation) and Country API tools
├── reflection.py        # Error detection, output validation, and recovery strategies
├── agent.py             # ReAct control loop (Reason -> Act -> Observe -> Reflect)
├── requirements.txt     # Python dependencies
└── README.md            # Complete project documentation & Viva preparation guide
```

## 📜 License
This project is open-source and created for educational and practical agentic AI engineering.
