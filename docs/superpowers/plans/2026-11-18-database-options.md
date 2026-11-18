# Database change: SQLite to MongoDB, a data-access API, and injection filtering (options, not a decision)

**Asked by Ben, 2026-11-18:** switch to MongoDB, connect it to the software through an API, and add input filtering so nobody can use SQL injection to reach the database.
**Status:** options and facts for Ben to decide. The assistant's recommendation is labelled; nothing has been changed in the code.

## Facts from the code (audited 2026-11-18)

| Fact | Value |
|---|---|
| Database today | SQLite, one file (`data/dev.sqlite`), standard-library `sqlite3`; ADR 0002 |
| Places that run SQL | 113 `execute` calls in 22 files under `src/` |
| SQL built from variables (f-string or concatenation) | 1: `src/purge/job.py:93` (`DELETE FROM {table} WHERE {where}`); both parts come from constants in the same file, not from a request. Two more are `executescript` of migration files |
| Every user-supplied value | passed as a bound `?` parameter (this is the standard defence against SQL injection) |
| Rules enforced inside the database | 11 triggers, 39 CHECK constraints, 36 foreign keys (migrations 0001 to 0009) |
| Tests that open the database directly | 109 files; the suite is 684 tests |
| Needs a database server today? | No. `./script/setup` creates the file in under a minute; the clean-machine run took 84 s |

## The skill's database-selection workflow, applied

| Question | Our answer | Points to |
|---|---|---|
| Structured with relationships? | Yes: reports, proposals, units, overrides and logs reference each other | SQL |
| ACID transactions required? | Yes: approving a proposal and assigning its unit must happen together or not at all (DEF-004) | SQL |
| Flexible or evolving schema? | No: nine migrations, a fixed model | SQL |
| Document-oriented data? | Slightly: the model's input and reasoning are JSON text | MongoDB (weak) |
| Scale | one laptop, hundreds of rows | SQLite or PostgreSQL |
| Consistency | strong consistency needed (a unit must never be double-booked) | SQL |

The skill's own rule for "under 1M records, single region" is PostgreSQL or MySQL, not a document store.

## What each safety rule would become in MongoDB (the important comparison)

| Rule today | In SQLite | In MongoDB (Community) |
|---|---|---|
| A unit is assigned only while its proposal is approved | trigger, cannot be skipped by any writer | application code inside a multi-document transaction (needs a replica set); any other writer can skip it |
| Override, tiebreak, reconciliation and sign-in logs cannot be edited | triggers | possible through database roles that allow insert and read only (a real equivalent) |
| Allowed values (severity, role, status) | CHECK constraints | `$jsonSchema` validators (field level only) |
| Links between records | foreign keys | none: application code |
| One active version per incident | partial unique index | partial unique index (a real equivalent) |
| A unit reserved by exactly one proposal | one atomic UPDATE | `findOneAndUpdate` (a real equivalent) |
| Delete incident data after 24 hours | purge job | TTL index (genuinely simpler) |
| Unit-status updates to every other agent, cached for a silent node | trigger on `units` | application code or change streams; more moving parts |

Net: about half the guarantees survive unchanged, three become "the application must remember", and nothing becomes safer against injection, because the application already uses bound parameters.

## Injection: what actually protects us

- **SQL injection** is prevented by bound parameters, which is already how all 113 calls work. Input filtering by itself is not the defence; parameter binding is. Filtering is a second layer.
- **MongoDB has its own version** (NoSQL operator injection: a request sending `{"$ne": ""}` where text was expected). The defences are the same shape: accept only the expected types and allow-listed fields, reject keys that start with `$` or contain `.`, never pass request JSON into a query, and give the application's database account the least privilege it needs.
- **Cheap, strong additions, whichever database:** (1) a test that scans the code and fails the build if any SQL string is built from variables, except the one reviewed purge line; (2) an allow-list validation layer at the web boundary (field names, types, lengths, character classes) with tests for injection-looking inputs; (3) a note in the runbook on database privileges.

## "An API between the software and the database"

- Today there is **no seam**: SQL is spread over 22 files. A data-access layer (a "repository" for each area: units, proposals, reports, accounts) is the right API to introduce. It is what makes any later change of database possible, and it is what a grader would call good architecture.
- A separate **network service** in front of the database is a different, heavier idea. It adds a process to start, another place to fail (slow, down, rate-limited, changed), and more to document. It is not justified for one process on one laptop.

## Practical constraints that decide timing

| Constraint | Effect |
|---|---|
| Milestone 13 (documentation, clean-machine test on a **borrowed laptop**) is due Sun Nov 22 | MongoDB needs a server (local `mongod`, or the cloud). The tester must install it inside the 60-minute clock, and a cloud database breaks the "no outbound calls" and offline rules |
| NFR-MNT-01 | a clean clone must reach a running app in under 5 minutes using only the README |
| 113 call sites and 109 test files | a rewrite is a multi-day job with the risk of breaking 684 passing tests |
| The documentation set Ben just chose | the architecture section 0 "surprise" (rules live in the database) and the ADR index would describe a system that no longer exists |

## Options (three ways forward)

**A (assistant's recommendation): keep SQLite for v1, and do the security work now, in a database-neutral way.** About 4 to 5 hours, no risk to Milestone 13.
1. Add the input-filtering layer and its injection tests (both SQL-looking and `$`-operator-looking inputs).
2. Add the "no SQL built from variables" scan as a test.
3. Introduce the data-access layer as a pilot for one module (for example units), leaving the rest, so a later swap is possible.
4. Write ADR 0009: "Keep SQLite for v1; MongoDB and PostgreSQL evaluated and deferred", with the table above as the evidence, and put the migration on the backlog.

**B: migrate to MongoDB anyway, on a separate branch, after Milestone 13.** Multi-day. Do the data-access layer first (A.3 for every module), then write the MongoDB adapter behind it, then port the triggers' rules into code and roles, then run the whole suite against it. Not before Nov 22.

**C: migrate to PostgreSQL instead.** Keeps relational integrity, triggers, constraints and transactions, and fixes the one-writer limit of SQLite. Still needs a database server (the same clean-machine problem), and it is also a multi-day port. It is the better "bigger database" if the real goal is a multi-user deployment.

## Questions for Ben
1. What is driving this: injection safety, scale, a multi-user deployment, learning MongoDB, or something a reviewer said?
2. Is it acceptable that the migration happens after Sunday's documentation milestone?
3. Should the data-access layer start now as a pilot (Option A.3)?
