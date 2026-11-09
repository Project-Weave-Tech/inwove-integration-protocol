<!-- The prompt for a follow-up reader. Used when earlier reports marked files partial or unread. The coordinator fills it and sends it to a {{model_reader}} agent. -->

You are a reader for the {{run_name}} reading project. First read the brief at `{{briefs_dir}}/reader.md` and follow it
exactly.

Slice: {{slice}}
Report path: {{report_path}}

Slice note: this is a mop-up of files earlier readers did not read to the end. {{slice_note}}

How to find your files. For each earlier report named above, open its Coverage table (the last section). Every file
it marks unread, partial or read only by search is yours, in the order the reports are named. If the note gives a
manifest for any of them, use it to find the paths.

For each file, read the part the earlier reader did not. For a file read only by search, read the whole file. For a
file read partly, you may start where the earlier reader stopped, but read to the end. Use repeated Read calls.

If a file is byte-identical to one that another reader read in full, or is the built form of a source file that
another reader read in full, you may say so after checking with a read-only command (a byte comparison or a hash)
instead of reading it again. Say which file and which reader.

Write to your report after every two or three files. In the report, say what the unread parts add: for test files,
the request and response documents the tests show (exact addresses, payloads and refusal codes); for other files,
anything not already in the earlier reports. Your Coverage table lists exactly what you read, with line ranges.
