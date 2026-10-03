# From backend to frontend

Messages from the backend session that the frontend session must know about. The git repository
is the only channel between the two sessions, so each message is a file here.

## For the frontend session

1. At the start of every session, after merging `main` (or the backend branch named in a message),
   read every `*.md` file in this folder except this one.
2. Do what a message asks, or write down in your worklog why you do not.
3. Delete the message file in the same commit that handles it. Do not delete a message you have
   not handled. An empty folder (only this file) means there is nothing to do.
4. If you disagree or need something else, add a file to `contracts/requests/` as described in
   `contracts/README.md`. Do not answer in this folder.

## For the backend session

- One file per topic, named `<yyyymmdd>-<short-slug>.md`, so two branches never edit the same file.
- Start with a status line: `Status: planned` (not in the contract yet) or `Status: ready`
  (merged, with the commit or branch). Update it when it changes.
- Say what changed, what the frontend has to do, and which contract operations and example files
  to look at. Keep it short, in English.
- Never edit or delete a message the frontend session still has to handle. The frontend session
  removes handled messages.
