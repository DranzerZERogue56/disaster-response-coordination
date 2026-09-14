# Requirements worksheet — staging area, not part of the submission

> Fill these in yourself, then move finished ones into `docs/requirements.md`.
> Each area below is a blank six-part template plus one generic prompting
> question — no requirement text, mechanisms, or behavior has been written
> for you. That's the line this milestone draws: I can ask, I can't author.
>
> Delete this file once everything's been moved over — it isn't a
> deliverable, it's scratch space so nothing risks corrupting the real file
> while you work.

---

## FR-INTAKE

**Prompting question:** What's the one specific thing the system does when
a report/data comes in from the field — who submits it, what do they
submit, and what happens if what they submit is bad or incomplete?

### FR-INTAKE-01 — `[ your short name ]`
**Priority:** `[ Must | Should | Could | Won't ]`
**Requirement:** `[ <Actor> shall be able to <action> <object> <condition>. ]`
**Rationale:** `[ why, which persona ]`
**Acceptance criteria:**
- `[ Given..., when..., then... ]`
- `[ Given <failure case>..., when..., then... ]`

**Source:** `[ ]`

---

## FR-AGENT

**Prompting question:** What's one specific decision a resource agent has
to make on its own, and what does it do when it isn't confident in that
decision?

### FR-AGENT-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## FR-COORD

**Prompting question:** When two agents want the same resource, or only
have part of the picture, what specifically has to happen for them to
reach a decision?

### FR-COORD-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## FR-RES

**Prompting question:** What's the actual, specific action for assigning
or reassigning a unit — who can trigger it, and under what condition?

### FR-RES-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## FR-DEGRADE

**Prompting question:** Name one specific way a piece of this system can
fail (a node, a model, a network link) — what does the system do the
moment that happens, specifically?

### FR-DEGRADE-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## FR-INFER

**Prompting question:** What's one specific, testable constraint on how
the local model runs (speed, hardware, version) that the system actually
enforces, not just hopes for?

### FR-INFER-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## FR-AUDIT

**Prompting question:** What specific decision needs a permanent, readable
record, and what does that record have to contain to actually be useful
later?

### FR-AUDIT-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## FR-SIM

**Prompting question:** What's the one specific thing you need the
simulation/playback capability to guarantee for testing or the demo?

### FR-SIM-01 — `[ your short name ]`
**Priority:** `[ ]`
**Requirement:** `[ ]`
**Rationale:** `[ ]`
**Acceptance criteria:**
- `[ ]`
- `[ ]`

**Source:** `[ ]`

---

## Cut from the original list (contradicted already-locked scope)

- ~~FR-AUTH — Role-based access control~~ — conflicts with `scoping-decision.md` §5 ("no multi-user accounts or role-based access")
- ~~FR-MAP — Zone boundary display / unit position tracking~~ — sounds like the live dashboard dropped in the Week 2 pivot
- ~~FR-ALERT — Responder notification dispatch~~ — not part of the designed system; this project produces a report, not live notifications
