# Scope Defense Memo

**To:** my instructor, standing in for the client who commissioned this system
**From:** Dranzer Rogue
**Date:** 2026-10-07
**Re:** `docs/plan.md` v0.1, in defense before you push back on it

Four things, as the assignment asks: defend the decision, argue the path I didn't take, name my weakest estimate, and give an honest accounting of where an assistant did and didn't do the thinking.

## 1. Defending the decision

Most students facing a 70.8h-over plan would cut a feature. I didn't. I raised the committed hours from the course's own default (87h, about 9.7h/week) to 150h, averaging 16.7h/week through the build phase. The obvious objection, and I'll say it plainly instead of waiting for you to: **promising more hours isn't a plan, it's wishful thinking with extra steps.** Anyone can write a bigger number in a capacity table. The number by itself proves nothing.

Here's why I'm standing behind it anyway: I gave you the idea of quality back in Week 1, and I intend to make good on it. This capacity increase isn't an unconditional promise — it's conditional on actually delivering. If I can't keep a consistent pace that shows consistent, accurate, quality results, I will start cutting features, not quietly let the schedule slip and hope nobody notices. The plan already names the mechanism for that: the calibration factor in `docs/plan.md` §4 is currently 1.00× on zero samples, because nothing's been built yet. The first real tasks in Week 9 change that. If the real ratio of actual-to-expected hours comes back meaningfully above 1.0, that's my signal the 150h commitment isn't holding, and the scope-decision table in §7 gets revisited for real — this time with an actual cut, not another capacity promise. The commitment is real, but it has a trip wire, not just a hope attached to it.

## 2. The path I didn't take

The cheapest single move available was swapping the Dispatcher Web UI for a CLI approval tool — about 10h net savings, and it would have closed most of the gap without betting on extra hours at all. I considered it seriously. The strongest case for it: it's less code, it reuses the same Decide Proposal interface either way, and a terminal prompt satisfies FR-AGENT-03's human-approval requirement just as validly as a web page does, on paper.

I decided against it because of who the Web UI is actually for. Not every dispatcher who'd use this system can work in a command-line tool, and I'm not willing to force that on them when a real front end can be intuitive instead. The two dispatcher personas this project is built around — the veteran dispatcher making real-time routing calls, and the data-skeptical dispatcher who wants to trust the system — are not people I should be asking to learn `curl` commands or memorize flags under pressure. Saving 10 hours of my own build time isn't worth shipping something the actual user of this release can't comfortably use. That tradeoff only favors the CLI if I only count my own hours and ignore the dispatcher's.

## 3. My weakest estimate

**T-5.2 — agent-node heartbeat detection, 3.00h.** It's also R-01 in the risk register: the first time I've ever run Mesa in a multi-process configuration, and I already flagged it as the project's biggest technical unknown before I even estimated it.

I'll change course on it the moment the math stops favoring the current approach: if fixing a hiccup in the cross-process heartbeat logic starts costing me more hours than switching to the fallback (a single-process, threaded "node" simulation, already named as T-5.2's own contingency) would cost to get the same result, I switch immediately instead of continuing to sink time into it. That's not a vague feeling — it's a direct hours comparison I can actually make in the moment. The hard deadline attached to it is the one already on the schedule: T-5.2 is built in Week 11 (`docs/plan.md` §5), and the 2-hour de-risking spike R-01 already calls for happens before I write the real implementation, not after. If the spike alone already shows the cost crossing over, I don't build the multi-process version at all — I go straight to the fallback.

## 4. The AI accounting

The assistant proposed all 39 tasks and all 9 risks in this plan — the task breakdown, the risk descriptions, the triggers and responses, the candidate hour ranges I was choosing between. I did not accept any of that as given. Every single O/M/P estimate and every L/I risk score is mine, supplied one at a time, not copied from a suggestion. I reviewed the full sorted-by-effort task list myself and tightened six estimates I decided were padded rather than genuinely hard. I made the real calls this week: raising capacity instead of cutting scope, and accepting the residual 14.1h buffer erosion honestly instead of quietly shrinking the buffer to make it disappear — the assistant flagged that exact temptation and I chose not to take it.

What I'm least sure of isn't any single number — it's whether my own prompting is actually getting me accurate, usable answers back, or whether I'm going to spend Weeks 9 through 11 discovering how much rework a misread instruction or a confidently-wrong AI suggestion costs me once real code is involved instead of a planning document. I will know the answer to that honestly by two things: the calibration factor computed from real logged hours against this plan's PERT estimates once Milestone 9's tasks start finishing, and a plainer measure I'm tracking myself — how much of my build time in Weeks 9-11 goes to fixing AI output that was wrong or misread what I actually meant, versus building the thing itself. If that cleanup time is small, my prompting and the AI's output are both holding up. If it isn't, that's the real number this plan was missing, not any of the 39 I already have.
