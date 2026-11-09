<!-- The review lead's findings file, phase 6. The review lead writes it at {{findings_path}}; the coordinator reads it before anything is pushed. -->

# Findings: <branches reviewed>

Written by the review lead. Most severe first. A finding is kept only if the lead checked it against the code and
can make it concrete: a branch, a file and line, the input that goes wrong and what comes out, and a fix small
enough for a helper to apply with a test. What the lead could not make concrete is dropped.

Severity marks: **MUST FIX BEFORE PUSH**, **SHOULD FIX**, **NOTE**.

## 1. <One-line title> (MUST FIX BEFORE PUSH)

- **Branch:** `feature/<name>`
- **Where:** `path/to/file:line`
- **What goes wrong:** the concrete input (for example, a document addressed to another recipient, sent twice, with
  this field missing) and the wrong outcome (for example, the server accepts it and writes a line).
- **Fix:** the change, small enough for one helper, and the test that proves it. Name the file the test goes in.

## 2. <One-line title> (SHOULD FIX)

- **Branch:**
- **Where:**
- **What goes wrong:**
- **Fix:**

## 3. <One-line title> (NOTE)

- **Branch:**
- **Where:**
- **What goes wrong:**
- **Fix:** or "no fix proposed", with the reason.

## Decisions for a person

Anything that is not a fix: a choice for the owner, for the security reviewer, or for the project's people.

## Not reviewed

What the lead did not read, and why (out of time, out of scope, no way to run it). Be specific enough that the next
reviewer knows where to start.
