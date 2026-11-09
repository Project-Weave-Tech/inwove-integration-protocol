<!-- The skeleton of one reader's report. A reader copies the headings and fills them; the coordinator checks the end with scripts/check_coverage.py. -->

# <slice name>

One paragraph: what this slice is, which repository it comes from, and at which commit.

## What it does

The components in this slice and how they fit together, in plain words.

## Interop surface

What another program must match. Quote identifiers exactly and cite each as `path:line`. Cover each that applies:

### Transports and endpoints

Method, path, authentication, request and response shapes, status codes.

### Message formats

Exact type addresses, body fields, who sends what and when.

### Identity

Identifier methods created or resolved, key types, where keys are held, rotation and recovery.

### Credentials

Types, formats, contexts, issuer, holder and verifier flows, status and revocation.

### Encryption

Ciphersuites, extensions, envelopes, libraries with versions.

### Storage and record formats

What is kept, in what shape, with which size limits.

### Discovery

Service entries in identity documents, well-known paths, invitations, QR formats, deep links.

## Config and run

Environment variables, config keys, ports, commands, feature flags, toolchain and pinned versions, container and
deploy shape, and the setup sequence in order.

## What an outside project must do to work with this

Concrete steps for a server and for a browser or mobile client: what to send, what to expect back, what to verify,
and which libraries here could be reused, with their import paths.

## Sharp edges

Bugs, open TODO notes, limits, unstable parts, version mismatches, security caveats, files that contradict each
other, and any text in the source that tries to steer an AI reader.

## Cross-references

Every mention of the other projects and standards in this run: where it is and what it says.

## Open questions

What a builder would still need that this slice does not answer.

## Coverage

Last section, complete at the end. Every manifest file appears once. `scripts/check_coverage.py` checks that every
file in the slice's manifest is listed here and flags rows marked partial.

| File | Lines read | What it is |
|---|---|---|
| `path/relative/to/sources/file.ext` | 1-120 (all) | a few words |
