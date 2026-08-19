---
name: pl-playwright-new-gui-old-gui-adjustment
description: Port a Playwright Page-Object-Model (POM) class for a PacketLight device's old web GUI into the equivalent class for the structurally-redesigned new web GUI, in the LightWatch_WEB repo (PL_Devices/PL_Pages/ -> PL_Devices/PL_Pages_New_Gui/). Use this whenever the user asks to create, port, adjust, or update a "*_new_gui.py" page-object file from its old-GUI counterpart, mentions doing the "old GUI vs new GUI" adjustment for a PL_Pages class, or names one of the PL_Pages_New_Gui files (PL_login_page_new_gui.py, PL_upper_panel_new_gui.py, PL_SNMP_page_new_gui.py, PL_security_page_new_gui.py, PL_main_screen_POM_new_gui.py, PL_performance_page_new_gui.py, etc.) as work to do next. Also trigger if the user says something like "do the same thing we did for X but for Y" in this repo, or asks to diff a PacketLight device's old vs. new GUI HTML to figure out what changed for a page object.
---

# Porting an old-GUI PL_Pages class to its new-GUI equivalent

You're adapting a Playwright POM class that drives a PacketLight device's **old**
web GUI (`PL_Devices/PL_Pages/*.py`, frame-based, e.g. `PL_LoginPage`) into the
equivalent class for that same device family's **new**, structurally-redesigned
web GUI (`PL_Devices/PL_Pages_New_Gui/*.py`, e.g. `PL_LoginPageNewGui`). The new
GUI is a real UI redesign, not a re-skin — some pages are byte-for-byte
identical, others moved fields into modals, converted tables to divs, or
replaced whole widgets. You cannot know which without looking at the live
device. Guessing from the class name or from general "modernization" patterns
will get you selectors that silently don't match anything.

## Inputs

Ask for whichever of these the user didn't already give you:

1. **Old GUI class file** — e.g. `PL_Devices/PL_Pages/PL_login_page.py`
2. **New GUI class file** — the file to create/update, e.g.
   `PL_Devices/PL_Pages_New_Gui/PL_login_page_new_gui.py` (may already exist as
   an empty stub or a partial skeleton with `pass` bodies — check before writing)
3. **Old GUI device IP** — e.g. `172.16.30.113`
4. **New GUI device IP** — e.g. `172.16.30.114`

Login credentials for both devices are always `tech` / `packetlight`. The web
UI form POSTs to `/goform/formLogin` with field **`username`** (not `user`) and
`password`.

## Step 1 — Read the old GUI class file completely

Read the whole file, not just the parts that look relevant. Note every method
signature, every locator/selector it uses, every frame it addresses (by
`page.frame(name=...)` or `frame_locator(...)`), and any cross-file imports
(e.g. `PL_login_page.py` importing `PL_upper_panel.py`). You need the full
picture before you can tell which selectors are safe to leave alone.

If the file already has a stub in `PL_Pages_New_Gui/` with the class/method
skeleton (matching signatures, `pass` bodies) — that skeleton is your target
shape; keep every method name and signature, fill in the adjusted bodies.

## Step 2 — Diff the live HTML before touching any code

Do not guess what changed. Do not assume "it's probably the same" or "it's
probably been modernized the same way as some other page you've seen." Fetch
the actual HTML from both devices for every ASP page / iframe the class
touches, and read it.

**Use `curl` with a cookie jar for this, not a real browser** — it's much
faster than driving Playwright/the browser tool for a page that doesn't need
JS execution, and it doesn't burn one of the device's limited concurrent web
sessions (these devices cap out at **8 concurrent sessions** — always
`GET /logout.asp` when you're done with a jar, or you'll eventually lock
yourself out).

```bash
JAR=/tmp/some_jar.txt
rm -f "$JAR"
curl -s -m 10 -c "$JAR" -b "$JAR" -X POST "http://<ip>/goform/formLogin" \
  --data "username=tech&password=packetlight" -o /dev/null
curl -s -m 10 -c "$JAR" -b "$JAR" "http://<ip>/<Some_Page>.asp" -o /tmp/some_page.html
rm -f "$JAR"
```

Fetch the SAME page from both devices and diff them (`grep`/`sed` for the
specific selectors the old class uses is usually faster than a full diff of
noisy machine-generated HTML — session cookies, CSRF tokens, serial numbers,
and JS counters will differ regardless and aren't signal).

If a page is reached by clicking through the UI rather than a known filename
(e.g. a tab inside a frame), you may need one authenticated Playwright
round-trip to discover the real filename/iframe name (view the frame's `.url`
or dump its `.content()`), then go back to plain curl for the rest of the
investigation.

**For a large class (many methods, many pages touched), delegate this
diffing step to a sub-agent (Task/Agent tool)** rather than doing it all
inline — it keeps your own context free for writing the actual code
afterward. Give the sub-agent a **precise, concrete prompt**: name the exact
ASP filenames if you know them, name the exact ids/selectors/attributes to
check for each page area, and ask it to report back exact selector-level
findings ("id X became a `<div>`, class Y's delete button lost its `value`
attribute") — not a vague "please compare the pages and summarize
differences." A vague prompt gets a vague, useless report back.

## Step 3 — Recognize the redesign patterns

This device family's new GUI applies a handful of patterns repeatedly across
otherwise-unrelated pages. Any given class will likely hit some subset of
these, not all of them — check for each one on the actual pages this class
touches rather than assuming which ones apply.

- **Frame reshuffle.** Elements can move to a *different top-level frame*
  than before, while the frame `name` attributes stay stable even when `id`s
  or nesting change. (Example seen in this device family: Logout/Refresh
  moved out of a nested `box_menu` frame into a new top-level `logo` frame;
  PSU/ExtAlarm/FAN moved into a new top-level `right_panel` frame.) Always
  match frames by `name`, and re-verify *where* a frame's content actually
  lives on the new GUI rather than assuming its parent didn't change.

- **Table → div.** A `<table id="X">` becomes a `<div id="X">` wrapping
  separate `<table id="thead">` (header) and `<div class="tbody"><table
  id="tbody">` (body) elements. The outer `#X` selector is usually still
  fine as-is since it's tag-agnostic — only a *child* selector that assumed
  a literal `<table>` tag needs the tag qualifier dropped (`table#X tr` →
  `#X tr`, or scope directly to `#tbody tr` for precision). Header rows use
  `<th>`, not `<td>` — if the surrounding code already filters rows by
  `td`-count, it will keep skipping the header for free. Don't "fix" a
  selector that still resolves correctly just because the underlying tag
  changed; verify first.

- **Modal relocation.** An "Add"/"Edit" affordance that used to be an inline
  last-table-row (or inline per-row fields) moves into a modal dialog. The
  modal's own JS **physically moves the modal's DOM node to the top-level
  page** on open — typically something like
  `(typeof parentFrame !== 'undefined' ? parentFrame : window.top).document.body.appendChild(modal)`.
  After clicking the button that opens it (still inside the original iframe),
  every field inside the modal must be addressed via the **top-level `page`
  object**, not the frame you clicked from — the frame-scoped locator will
  find nothing. Confirm this empirically (open the modal in a quick Playwright
  script, check `page.locator(...)` vs the frame locator) rather than
  assuming the relocation target. Write a **dual-path** implementation: try
  the modal-open button first, fall back to the old inline-field flow if
  the button isn't found, so the method still works for any product/page
  that never got migrated to the modal.

- **Submit button → image/plain button.** `<input type="submit"
  value="Delete">` becomes `<input type="image">` or a plain `<button>`
  with **no `value` attribute at all**. Drop `[value='...']` from any
  selector that assumed one.

- **Enable/Disable pair → single toggle.** Two buttons (or a button whose
  `value` flips) become one `<input type="checkbox">` wrapped in `<label
  class="custom-toggle">`. The raw checkbox has a **zero-size bounding box**
  from the toggle-switch CSS — `.check()`/`.uncheck()`/`.click()` on the
  checkbox itself fail with "element is not visible" *even with
  `force=True`*. You must click the **wrapping label**, not the checkbox.
  Read the checkbox's `checked` state (that's just a DOM property read, no
  visibility needed) to decide whether a click is even necessary before
  toggling.

- **Tag change on a form field.** A field keeps its `name`/`id` but changes
  tag (seen: `<input type="text">` → `<textarea>`). Use a tag-agnostic
  attribute selector (`[name='x']` instead of `input[name='x']`) so the
  same code works against either GUI version.

- **Dropdown restructuring.** Two related selects can get merged into one
  combined control with a different value encoding (seen: separate hour/
  fraction timezone selects merged into one `h_m`-valued select). Write a
  small parse/format adapter so the *caller's* input format doesn't have to
  change, rather than pushing the new encoding up to every call site.

If you find a pattern that isn't in this list, that's fine — these are
*things to check for*, not an exhaustive spec of the redesign. Note it in
your report to the user; it's worth them knowing about for the next file.

## Step 4 — Write the new-GUI file

- Copy the old file's structure. Rename the class with a `NewGui` suffix
  (`PL_LoginPage` → `PL_LoginPageNewGui`).
- Update cross-file imports to their `PL_Pages_New_Gui` equivalents (e.g.
  `from PL_Devices.PL_Pages.PL_upper_panel import PL_Upper_Panel` →
  `from PL_Devices.PL_Pages_New_Gui.PL_upper_panel_new_gui import
  PL_Upper_PanelNewGui`, and the corresponding `self.upper_panel = ...`
  assignment).
- Apply **only** the adjustments you actually confirmed in Step 2/3. Leave
  everything else byte-for-byte identical — same method names, same
  signatures, same retry/timeout patterns, same docstrings. This file's job
  is to be a drop-in replacement for the old class against the new device,
  not a rewrite.
- **Deprecated `_old`-suffixed methods** already present in the source file
  (e.g. `add_new_user_old`, `set_admin_status_old`) are ported as-is,
  unmaintained, matching the source file's own convention of keeping them
  around as unadjusted reference code. If your Step 2 investigation shows
  one is now definitely broken on the new GUI, say so in a one-line comment
  above it — don't fix it, and don't silently leave the misleading
  impression that it still works.
- Respect this repo's `# ✅` convention: a comment directly above a method
  means "verified against real hardware." Only add it where **you**
  verified the method in Step 5 below. Do not carry over a `✅` from the old
  file onto an adjusted method without re-earning it.

## Step 5 — Verify live against the real new-GUI device

Write a throwaway Python script (not one of the repo's own `PL_Tests/`
files) that imports the actual new class and exercises its methods against
the live new-GUI device, printing pass/fail per step. Run it with the
`.venv311` interpreter — `./.venv311/Scripts/python.exe path\to\script.py`
— since `.venv` (3.14) may be missing Playwright's browser binaries while
`.venv311` has them. Route long-running scripts through the background-task
mechanism rather than blocking the conversation on them.

### Triage every method before you script it

Classify each method before writing a single test line:

- **Safe / read-only** (navigation, table reads, "get" methods) — always
  test these directly.
- **Reversible with cleanup** (add-then-delete a disposable test entity —
  a throwaway SNMP trap manager IP, a throwaway user account) — test these,
  and make sure your script deletes the entity again even on a failure path
  (don't leave test residue on a shared lab device).
- **Destructive or unsafe on shared infrastructure** — rebooting the
  device, flipping a live port's admin status/service type/provisioning,
  changing time-sync config, anything with **no available rollback method**
  (e.g. you can add an SNTP server but the class has no method to remove
  one). **Skip live-testing this category.** Still write the best-effort
  adjusted code from your Step 2/3 findings, but do not click the real
  button. Mark it clearly: no `✅`, plus a short comment explaining why it
  wasn't exercised (what's at risk, and what would need to be true to test
  it safely — e.g. "verify on a known-idle port first").

This device family is real lab hardware, potentially shared with other
people's in-progress work — treat every mutating action with the same
caution you'd want someone to apply to something you were relying on.

### When something fails

Don't assume a verification failure means your ported code is wrong. Rule
out test-script mistakes first:

- A parameter combination the GUI itself disallows (e.g. picking an SNMP
  "No Access" auth level, which the page's own JS then disables the Priv
  dropdown for, and your test script also tries to set Priv).
- Bad test ordering — navigating to a different tab in an earlier step,
  then assuming a later step's "click the already-active panel button"
  call will reset to a default sub-tab. Some panel buttons no-op if the
  panel item is already selected, leaving a stale tab active from a
  previous step. Test the suspect method in isolation (fresh login, single
  call) before concluding the port itself is broken.
- If a mutating test call actually did leave the live device in a changed
  state (e.g. it returned `False` but the value was actually applied, or a
  quirky comparison masked a real change), diagnose exactly what changed
  and restore the original value before moving on — and say so plainly when
  you report back, don't bury it.

## Step 6 — Report back

Summarize, grouped by what actually happened, not method-by-method prose:

- **Unchanged** — carried over verbatim, no adjustment needed (and why you're
  confident: usually "confirmed identical HTML on both devices").
- **Adjusted and verified live** — what changed structurally, what you did
  about it, and that you confirmed it working against the real new-GUI
  device.
- **Adjusted but not safe to verify live** — what changed, what you did
  about it, and the specific reason you didn't click the real button
  (what's at risk on shared hardware).
- **Anything you broke and fixed** — be upfront about any accidental
  mutation during testing and how you restored the device.

Then ask whether to continue with the next file, if there's an obvious next
one (e.g. the sibling files in `PL_Pages_New_Gui/` that are still empty
stubs).
