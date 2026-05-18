# Concept Interaction Submission: EvoAtlas

## Project Choice

**Concept name:** EvoAtlas: AI-Assisted Pokemon Evolution Explorer

**Murray participatory model:** Tool

**PokeAPI information space:** Evolution

**Human-AI interaction goal:** EvoAtlas helps a user explore Pokemon evolution chains by entering natural-language constraints such as "Which Eevee evolution needs no trade and no item?" or "How do I evolve Eevee into Sylveon?" The AI does not act like a character or companion. It acts as a reasoning tool that translates the user's goal into evolution constraints, highlights valid and blocked branches, and generates a step-by-step plan.

## PDF Page Plan

### Page 1: Concept Overview

Include:

- Title: **EvoAtlas: AI-Assisted Pokemon Evolution Explorer**
- Participatory model: **Tool**
- Information space: **Evolution**
- One-sentence purpose: **EvoAtlas turns complex Pokemon evolution rules into a visual, filterable map with AI explanations.**
- Screenshot or export: `evoatlas_storyboard_triptych.svg`

Short description to paste:

> EvoAtlas is a human-AI interaction for exploring Pokemon evolution chains. The user asks a goal-based question, and the system transforms it into visible constraints such as trade, item, friendship, time of day, known move, gender, and location. The interface then shows which evolution paths match, which paths are blocked, and what steps the user should take next.

### Page 2: Low-Fidelity Process

Use the rough sketch / early board:

- `evoatlas_crit_sketch_2panel.svg`

Annotate these design choices:

- The early taxonomy sketch organizes evolution rules into categories before designing the final screen.
- Eevee was chosen as the example because one Pokemon has many branches with different trigger types.
- The sketch separates the information space from the interface so the design is based on domain structure, not only visual layout.
- The AI role is shown as a constraint interpreter: it reads the user's question and maps it to evolution conditions.

Caption to paste:

> The low-fidelity design phase focused on understanding the Evolution information space. I first grouped evolution triggers into categories: mechanical triggers, inventory triggers, bond/friendship triggers, contextual triggers, and complex multi-condition triggers. This helped me design an interface where the AI can explain evolution logic instead of only returning a single answer.

### Page 3: Medium-Fidelity Process

Use the middle/interface portions of:

- `evoatlas_storyboard_triptych.svg`

Annotate these design choices:

- Search bar supports natural-language exploration.
- Filter chips make hidden constraints visible.
- Branch map shows the structure of the evolution chain.
- Blue paths mean valid branches.
- Gray paths mean blocked branches.
- AI analysis panel explains why a path matches or fails.
- Plan button turns exploration into action.

Caption to paste:

> In the medium-fidelity version, I moved from taxonomy to interaction. The main screen combines a natural-language query, visible constraint chips, an evolution branch map, and an AI analysis panel. This makes the AI's reasoning visible, so the user can understand the information space instead of blindly accepting a result.

### Page 4: High-Fidelity Resolution

Use the phone preview / polished board:

- `evoatlas_storyboard_triptych.svg`

Annotate these final UI decisions:

- Dark header creates a focused app identity.
- Evolution map is the main object because the domain is relational.
- Color coding separates possible and impossible choices.
- AI explanation is placed beside the map so reasoning stays connected to the branch it explains.
- The step-by-step plan turns the selected evolution path into a usable checklist.
- The design uses tool language like **filter**, **match**, **blocked**, **recommended**, and **plan** instead of conversational personality language.

Caption to paste:

> The high-fidelity version resolves the concept into a polished mobile-first tool. The user can search, compare branches, inspect reasons, and generate an evolution plan. The interface prioritizes clarity, visible constraints, and fast comparison across possible outcomes.

## Final Interaction Flow

1. The user opens EvoAtlas and enters a question such as **"Which Eevee evolution needs no trade and no item?"**
2. The AI parses the question into constraints: **Pokemon = Eevee**, **no trade**, **no item**.
3. EvoAtlas displays the full Eevee evolution branch map.
4. Matching paths are highlighted in blue, while blocked paths are grayed out.
5. The AI explanation panel explains why each branch is valid or blocked.
6. The user selects **Sylveon** as the recommended path.
7. EvoAtlas generates a checklist: keep Eevee in party, raise friendship, teach a Fairy-type move, then level up.

## Annotated Design Choices

**Natural-language input:** Lets users ask goal-based questions without needing to know the exact PokeAPI field names.

**Constraint chips:** Shows the user what the AI understood from the prompt, supporting visibility of system status.

**Evolution branch map:** Represents the Evolution information space visually, making relationships easier to understand than a flat list.

**Color-coded paths:** Helps users immediately distinguish valid paths from blocked paths.

**AI analysis panel:** Explains the reasoning behind the result so the user can learn the domain rules.

**Plan checklist:** Converts an abstract evolution rule into a concrete action sequence the user can follow.

**No AI persona:** Keeps the interaction aligned with the Tool model. The AI is useful because it filters, explains, and organizes, not because it roleplays.

## Participatory Justification Paragraph

EvoAtlas aligns with Murray's **Tool** participatory model because the user directly controls the task and the AI extends the user's ability to inspect a complex information space. The user can ask a question, adjust constraints, compare possible branches, select a target evolution, and request a plan. The AI does not behave like a companion, game opponent, or autonomous machine; it acts as an instrument for filtering, mapping, and explaining evolution data. The interaction answers "What can I do?" by giving the user concrete operations: search with natural language, see parsed constraints, inspect valid and blocked paths, compare outcomes, and turn a selected path into a checklist.

## Encyclopedic Justification Paragraph

EvoAtlas maximizes encyclopedic affordances by exposing the boundaries and internal structure of the Pokemon Evolution information space. Instead of treating evolution as isolated facts, the interface organizes the domain around chains, branches, trigger types, required items, friendship levels, moves, time conditions, trade requirements, gender requirements, and location requirements. The evolution map shows how one Pokemon can connect to many possible outcomes, while the AI explanation panel explains why each path belongs inside or outside the user's current constraints. This makes the domain feel explorable and complete: users can understand not only the answer, but also the shape, limits, and rules of the evolution system.

## Rubric Coverage Checklist

**Design Process - 15 pts**

- Low-fidelity taxonomy sketch included.
- Medium-fidelity interface sketch included.
- High-fidelity polished storyboard included.
- Process shows movement from domain structure to interaction layout to final look and feel.

**Idea Quality - 10 pts**

- The concept explores evolution in a new way through constraint parsing, branch visualization, and AI explanations.
- The interaction is more than a search box because it helps users understand rules and compare possible paths.

**Participatory Justification - 5 pts**

- Chosen model is clearly stated as **Tool**.
- Paragraph explains what the user can do and how the AI supports those actions.

**Encyclopedic Justification - 5 pts**

- Chosen information space is clearly stated as **Evolution**.
- Paragraph explains the boundaries of the domain and how the design reveals them.

**Check++ / Extra Credit Target**

- Include both SVG boards in the PDF.
- Add arrows or labels in the PDF pointing to the search, chips, map, AI explanation, and plan checklist.
- Create a simple clickable Figma prototype with at least three frames: Search, Results Map, and Plan Checklist.
- Record a short walkthrough video explaining the prototype and the two justification paragraphs.

## Figma Prototype Frame List

Frame 1: **Ask an Evolution Question**

- Search field: "Which Eevee evolution needs no trade and no item?"
- Empty branch-map area waiting for results.
- Helper text: "Ask by Pokemon, goal, or restriction."

Frame 2: **Evolution Branch Map**

- Center node: Eevee.
- Branch nodes: Vaporeon, Jolteon, Flareon, Espeon, Umbreon, Leafeon, Glaceon, Sylveon.
- Blue highlighted branch: Sylveon.
- Gray blocked branches: item or trade paths.
- Right panel: AI Analysis explaining the match.

Frame 3: **Sylveon Plan**

- Header: "Plan: Eevee -> Sylveon"
- Checklist:
  - Have Eevee in party.
  - Raise friendship to at least 160.
  - Teach a Fairy-type move.
  - Level up Eevee.
- Callout: "Why this works: Sylveon matches no trade and no item, but requires friendship plus a Fairy move."

## 45-Second Video Script

> My concept is EvoAtlas, an AI-assisted Pokemon Evolution explorer. I chose Murray's Tool model because the AI works like a reasoning instrument, not like a companion or game character. The information space is Evolution. I started by sketching the taxonomy of evolution triggers, then moved into a medium-fidelity interface with search, filters, a branch map, and an AI explanation panel. In the final prototype, the user asks which Eevee evolution needs no trade and no item. EvoAtlas parses the question into constraints, highlights valid and blocked branches, and recommends Sylveon with a step-by-step plan. This maximizes encyclopedic affordance because users can see the structure and boundaries of the evolution domain, not just one answer.
