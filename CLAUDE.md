# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Playwright-based (Python, **sync API**) UI automation for PacketLight's **LightWatch WEB** network management application, plus automation for the individual **PL (PacketLight) device** web GUIs that LightWatch manages, plus a set of standalone SNMP/QC integration scripts that are launched from HP ALM / Quality Center. There is no application source here — this repo only drives and verifies external systems (a LightWatch server and physical/virtual network devices reachable on the lab network, e.g. `172.16.x.x`).

## Environment / running scripts

- Two virtual envs coexist: `.venv` (Python 3.14, primary/default interpreter) and `.venv311` (Python 3.11). Switch with `.venv\Scripts\activate` or `.venv311\Scripts\activate`. In VS Code, use `Python: Select Interpreter`.
- Dependency lists live in `Requirements/requirements_314.txt` and `Requirements/requirements_311.txt`. **These files are UTF-16LE encoded** — reading them as UTF-8/ASCII will show mojibake; use an encoding-aware read (e.g. `Get-Content -Encoding Unicode` or Python `open(path, encoding='utf-16')`).
- There is no pytest config (`pytest.ini`/`conftest.py`) and no test runner wiring, despite files being named `test_*.py`. Every file under `Tests/`, `PL_Devices/PL_Tests/`, and the per-feature `PythonScripts/` folders under `Scripts/` is a **standalone script**: it builds its own Playwright browser/context/page in `if __name__ == "__main__":`, prints ✅/❌ per step, and is run directly:
  ```
  python Tests\test_login.py
  python PL_Devices\PL_Tests\test_PL_login.py
  python Scripts\Device_Discovery\SNMP\PythonScripts\start_discovery_for_ip_range_SNMPv3.py [optional_parameters_file_path]
  ```
  A stale `Tests/.pytest_cache/` shows pytest was used at one point against a different (now-removed) file naming convention (`test_login_pytest.py`) — don't assume that convention is current.
- Scripts default to hardcoded lab constants (server IP, credentials, device IPs) at the top of the file when run with no args. When an ALM parameter-file path is passed as `argv[1]` (see `Scripts/*/ParametersFiles/*.txt`), the script `eval()`s the file's contents as a Python dict literal and does `globals().update(const_dict)` to override those constants — parameter files are trusted local input, not external/untrusted data.

## Architecture

### Two parallel Page-Object hierarchies

- `Pages/` — POM for the LightWatch WEB app itself (Angular front end: locators target components like `app-input`, `app-sidenav`, `[routerlink=...]`). One file per major nav section (`login_page.py`, `device_discovery.py`, `domain_management.py`, `network_topology.py`, `alarms_and_events.py`, `inventory.py`, `performance.py`, `service_list.py`, `service_provisioning.py`, `system_configuration.py`, `system_operations.py`, `task_manager.py`, `user_management.py`), plus `left_panel_page.py` (main nav) and `upper_panel.py` (header).
- `PL_Devices/PL_Pages/` — POM for the legacy, frameset-based PacketLight device GUI (each device has its own embedded web server) — `PL_login_page.py`, `PL_main_screen_POM.py`, `PL_SNMP_page.py`, `PL_security_page.py`, `PL_upper_panel.py`. These devices use old-style `<frame>`/`<iframe name="...">` navigation (e.g. `horizontal_menu_frame` → `box_menu`, `vertical_menu_frame`, `main_page`), so locators are built through chained `page.frame_locator(...)` calls rather than flat selectors.
- Tests/scripts frequently need **both** hierarchies at once: e.g. driving LightWatch's Device Discovery to add a device by IP, then opening a *second* Playwright page (`page.context.new_page()`) to log into that same device's own GUI directly and verify state there (SNMP trap config, user list, etc.).

### `Utils/`

- `utils.py` — cross-cutting helpers used by both POM hierarchies and scripts: `create_page()` (standard browser/context/page factory, default viewport 1920×937 @ scale 1 — treat this as the canonical way to open a page so screenshots/layouts stay comparable across scripts), `refresh_page()`, `create_frame_html()` (dumps every frame's HTML to `frames_dump/` for debugging frame-based PL device pages), `countdown_sleep()`/`countdown_timer()` (visible wait timers), `click_system_btn()`/`click_maintenance()`/`device_restart()` (Playwright ports of the legacy PL device "System → Maintenance → Restart" flow, operating through frame chains), `Device_Is_Up()`/`devices_are_up()`/`http_ping()` (poll a device/LW host back up after a restart, with `wait4ever` and concurrent multi-device modes).
- `Logger.py` — `create_logger(root_directory, log_file_name, directory_name=None)` creates a timestamped run folder (`HHMMSS_ddmmyy_run/`) per invocation and returns a configured file logger; used by the longer QC scripts to persist a run log alongside console output.
- `map_locators.py` — `MapLocators`, a focused locator helper for the Management Map / Network Topology SVG map view (event filters, zoom controls, lock/save/discard, tabs), used from `Pages/network_topology.py`.

### `Scripts/` — HP ALM / Quality Center integration

Organized by functional area (`Alarms_And_Events/`, `Device_Discovery/`, `Domain_Management/`, `Inventory/`, `Network_Topology/`, `Performance/`, `Service_List/`, `Service_Provisioning/`), and within `Alarms_And_Events/` further split by sub-feature (`Chassis_Alarms`, `Chassis_Events`, `Device_Alarms`, `Device_Events`, `Non_PacketLight_Devices`, `SNMP_Traps`). Each leaf feature folder follows the same 3-subfolder shape:
- `Design/` — plain-text/markdown step-by-step spec the script was written from (numbered steps, exact expected UI values). Treat these as the source of truth for intended behavior/edge cases when modifying the matching script.
- `ParametersFiles/` — one or more `*_Parameters.txt` files: Python-dict-literal text consumed via `eval()` when the script is launched with that file's path as an argument (this is how ALM/Quality Center parameterizes runs per test case).
- `PythonScripts/` — the actual executable script(s) for that feature.

`Scripts/QC_Launch_Example.py`/`.txt` document the QC launch mechanism: Quality Center runs a VBScript wrapper (`Test_Main`) that shells out to a dedicated venv's `python.exe` with the target script and a parameter-file path, then reads back a `%temp%\TD_80\output.txt` results file (`status;actual_value` per line, one per ALM test step) and attaches any files placed under `%temp%\TD_80\PythonAttachments`. `QC_Launch_Example.py` also shows a `run_step()` convention (try the step, print/log Pass/Fail, optionally record to an ALM report via `Utilities.QCreporter`) and an SNMPv3 discovery combinatorics test — note `Utilities.QCreporter` isn't part of this repo (it's expected on the QC launch machine's environment), so don't assume it's importable when running scripts locally without a QC parameter file.

### Other directories

- `frames_dump/` — output-only; HTML dumps written by `Utils.utils.create_frame_html()` for inspecting live frame structure when a locator chain isn't matching.
- `Docs/`, `Text_files/`, `Images/` — reference material (venv setup steps, project structure notes, screenshots) — background context only, not code.
- `Old_Files/`, `Tyuta/` — legacy/experimental, not part of the active suite.

## Conventions worth preserving when editing

- Page-object methods generally return `bool` (or `Tuple[bool, str]` for actions with a message, e.g. `device_restart`) rather than raising, so calling scripts can log a Pass/Fail per step and continue; exceptions are usually caught internally and turned into a `False`/print rather than propagated. Match this style in new POM methods rather than switching to bare asserts inside `Pages/`/`PL_Devices/PL_Pages/`.
- Assertions/`raise AssertionError` are used at the *script/test* level (calling code), not inside POM classes.
- A `# ✅` comment above a method means it's been verified working against real hardware/LW — don't remove it when lightly touching a method, and add it once you've similarly verified a new one.
