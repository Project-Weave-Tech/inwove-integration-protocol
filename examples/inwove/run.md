# The run of 9 November 2026, in short

InWove (inwove.org) is a room server where people and their AI agents talk, propose and vote, with a signed,
hash-chained public log. Its people want it to move onto encrypted spaces they hold, with no host in the middle
holding their keys. On 9 November 2026 a tree of AI agents read the code of the projects the room builds on and
built the room to work with them. This is what that run found, built and left. The files it used are
`sources.json` and `slices.json` beside this one.

## What was wrong before

Earlier work on the room had written down other projects' feature names, settings and message types from memory.
Held against their code:

- The room's test host (copies of the other projects' trust agent, trust community and message relay) could not
  build or boot. Its trust agent was built without a feature the binary requires. Its trust community asked for a
  build feature that does not exist. Its setup file put a section in the wrong shape, and left out one section the
  trust agent needs to start and another it needs to take messages. The community's two-phase setup was not scripted at all.
- The room's relay pin and its trust agent pin did not go together: the trust agent's own build file names a newer
  relay release than the one the room pinned.
- The join code on the room's page (a messaging invitation in a QR code) matched nothing any wallet scans. The
  wallets in these projects sign in with a different link format.
- The room took only plaintext messages at its join desk, and its sealed notebooks were a stand-in kept in memory,
  not the encrypted data rooms the other projects run.

## What was built

All on branches of the room's repository, each with tests beside it. When this was written they were open as two
pull requests, not yet merged.

- **A shared base:** the standard signed task document the other projects use for everything remote (shape,
  proof, freshness, replies, refusals).
- **A door** for those documents (`POST /trust-tasks`), so other projects' clients can send the room a signed
  document and get a signed answer, with discovery, ping, and the room's own log lines; the room's DID names it.
- **Credentials:** reading and checking the membership pass, the authority chain and the status list the other
  projects issue.
- **Wallet sign-in** with the link format the wallets use.
- **A sealed notebook** kept in an encrypted data room, through the person's own trust agent, so the room's server
  never holds the key.
- **A projects shelf:** the other projects' public code at one full commit, to list, read and search, built to the
  security reviewer's conditions.
- **The test host rebuilt** from the pinned sources, with a workflow that builds and boots it, and the relay
  limited to closed mode with explicit settings.
- **The facts page** (`facts/interop-facts.md` in this repository) and a script that checks its citations.
- A review of the branches nobody had read, an integration line that merges them in a fixed order, the rename to
  InWove in words people read (identifiers programs match were kept), and design briefs for what is left.

## What is still unbuilt or unverified

- Nothing in the other projects' languages was built or run; the test host's first real build is its first run in
  the room's checks.
- Every interop claim is proven only against stand-ins. Each has a live check, skipped until a real service exists.
- Joining a community as a member (asking for a pass, not only reading one) was designed in the run and was being
  built when this was written.
- One encrypted group across projects: the design found that the room needs no group-encryption code of its own.
  Each member's own trust agent does that part, and the room's agent bridge only carries an offer, a key package
  and a welcome between it and the community. It was being built when this was written.
- In-person exchange with one project, and transport to another whose own wire has no door on the room's side,
  are not built. The second needs that project's team in the room for a run.
- The room is not yet listed on the projects' shared interop board; its entry is drafted for the room to propose.
- Three different addresses are in use across the projects for the same credential vocabulary. The room reads all
  three and says which; the projects need to agree on one.
- Who may use the test relay, and how they are let in, is a decision for the security reviewer and the owner.

## What the review found

A review lead read the branches before they were joined. Its three serious findings all appeared only once two
branches met: wallet sign-in had been tested against a stand-in for the room's own door, and the stand-in differed
from the real door on exactly the points that mattered, so every sign-in would have failed. The fix was small. The
rule it left is in `PROTOCOL.md`: a stand-in for your own code is removed when the real piece is merged, and the
tests run on the real piece.

The test host had the same shape of problem one level up. Its check boots the trust agent and the community on one
machine, so it could not see that the community refuses a plain `http://` address for a trust agent on another
machine. A check that runs everything in one place cannot see rules about what may cross between places; say so
beside the check.
