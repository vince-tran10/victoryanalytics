---
description: Process a new Party & Boxes export end to end (re-score, team check, rebuild + publish the guide)
argument-hint: <path to export .txt> [--beat fight,...] [--fight boss|none] [--staging A-B --active N]
---
Follow CLAUDE.md. Process the export: $ARGUMENTS

1. Run `python3 scripts/team/update.py $ARGUMENTS` from the repo root.
2. Check the printed box layout ("around Active start"). If the staging box or Active start is wrong, re-run with
   `--staging A-B --active N`.
3. Publish `output/chapter8_report.html` with the Artifact tool to the URL in `workspace/team/state.json` ("artifact").
4. Append 2–5 lines to NOTES.md (what changed), then commit and push to the current branch.
5. Reply to Vincent in short bullets: new catches and verdicts, green/red box moves, To do cards, the team verdict
   (rank and gap from the team search), anything that needs his decision.
