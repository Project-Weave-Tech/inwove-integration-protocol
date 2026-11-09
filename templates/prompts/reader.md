<!-- The prompt for one reader, one slice. The coordinator (or scripts/render_run.py) fills the slice values and sends it to a {{model_reader}} agent. -->

You are a reader for the {{run_name}} reading project. First read the brief at `{{briefs_dir}}/reader.md` and follow
it exactly.

Slice: {{slice}}
Manifest: {{manifest_path}}
Report path: {{report_path}}

Slice note: {{slice_note}}

The slice note says what this slice is and what to look for. If it states an exception to the reading rule (for
example, files too large to read in full), the exception applies to the files it names and to nothing else. Say in
your coverage table exactly which line ranges you read for each such file.
