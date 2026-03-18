"""
reporting/clause_1_1_1.py
─────────────────────────────────────────────────────────────────────────────
Report generator for ITSAR 1.1.1 — Management Protocols Entity Mutual Auth.

Real result format (from the live runner)
──────────────────────────────────────────
    {
        'name':        'TC1_MUTUAL_AUTHENTICATION',
        'description': 'SSH first connection mutual authentication',
        'steps':       [],          # always empty — YAML is the source
        'status':      'PASS',      # or 'FAIL'
        'evidence': [
            {
                'command':    'ssh ...',                     # str or None
                'output':     '┌──(myenv)─(kali㉿kali)...',# str or None
                'screenshot': 'output/runs/.../screenshots/file.png'  # or None
            },
            ...
        ]
    }

TC name mismatch between runner and YAML spec
──────────────────────────────────────────────
The runner uses short names derived from class names, e.g.:
    TC3_SSH_INVALID_CREDENTIALS   (runner)
    TC3_MUTUAL_AUTHENTICATION_SSH (YAML spec)

The YAML spec has an optional `runner_name` key per test case so the
generator can match runner output to the correct spec entry:

    testcases:
      TC3_MUTUAL_AUTHENTICATION_SSH:
        runner_name: TC3_SSH_INVALID_CREDENTIALS
        ...

Without `runner_name`, matching is attempted by position (TC3 → third entry).
The report always uses the YAML canonical name for display.

Duplicate TC names in results
──────────────────────────────
TC8 appears twice in real output (TLS 1.0 and TLS 1.1 share the same name
because of a runner naming collision). Both evidences are merged into one
execution block; the last status wins. The YAML spec should have separate
canonical entries (TC8 + TC9) with appropriate runner_name mappings.

Partial runs — what happens
────────────────────────────
If only N of M defined test cases were executed:

  ┌──────────────────────────────────────────────────────────────────────┐
  │ Section 10 (Test Execution)                                          │
  │   • Displays a red NOTE at the top: "N of M cases run."             │
  │   • Only renders the cases that actually ran (no blank stubs).       │
  ├──────────────────────────────────────────────────────────────────────┤
  │ Section 11 (Result Summary)                                          │
  │   • Shows ALL M cases in YAML order.                                 │
  │   • Ran cases → green PASS or red FAIL cell.                         │
  │   • Not-run cases → grey NOT RUN cell.                               │
  │   • Totals row shows  "XP / YF / ZNR"  so the gap is immediately    │
  │     visible to the reviewer.                                          │
  ├──────────────────────────────────────────────────────────────────────┤
  │ Section 12 (Conclusion)                                              │
  │   • Adds an extra bold NOTE bullet listing how many weren't run.     │
  │   • Overall result banner is FAIL (incomplete run ≠ passing eval).   │
  └──────────────────────────────────────────────────────────────────────┘

Entry point
───────────
    context = {
        'clause':     '1.1.1',
        'run_dir':    'output/runs/2026-03-13_10-10-42-1.1.1',
        'dut_info':   {...},    # from get_dut_info()
        'start_time': '13/03/2026',
        'end_time':   '13/03/2026',
    }
    results = [...]   # list of result dicts above

    path = Clause111Report(context, results).generate()
─────────────────────────────────────────────────────────────────────────────
"""

import os
import re
from docx.shared import RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from icaf.reporting.helpers import (
    # colours
    PURPLE, LIGHT_PURPLE, PURPLE, DARK_GREY, MID_GREY,
    TABLE_HEADER_BG, TABLE_ALT_BG, PASS_GREEN, FAIL_RED, WHITE,
    NOT_RUN_COLOR, NOT_RUN_BG,
    HEX_PURPLE, HEX_PASS_GREEN, HEX_FAIL_RED,
    # low-level helpers (used in _build_summary_table)
    _style_cell, _para_in_cell, _set_table_width, _set_col_widths,
    # paragraph builders
    section_heading, sub_heading, tc_heading,
    body_para, label_value_para, bullet_item, numbered_item,
    spacer, terminal_block, add_screenshot, status_result_table,
    # table builders
    two_col_info_table, four_col_header_table,
    # page-level builders
    build_front_page, build_doc_with_header_footer,
)
from icaf.reporting.spec_loader import load_clause_spec


# ── Unified accessor (dict or object) ─────────────────────────────────────────

def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


# ── Output cleaner for terminal text ─────────────────────────────────────────

def _clean_terminal_output(raw: str) -> list:
    """
    Takes raw terminal output (may contain Kali box-drawing chars, ANSI
    escapes, trailing blank lines) and returns a clean list of strings
    ready for terminal_block(), capped at 40 lines.

    Specifically:
      • Strips ANSI escape sequences
      • Strips leading/trailing blank lines
      • Keeps at most 40 lines (truncates with a note if longer)
    """
    if not raw:
        return []

    # Strip ANSI escape codes (colour, cursor movement, etc.)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub("", raw)

    lines = text.splitlines()

    # Strip leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    # Strip trailing blank lines
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return []

    if len(lines) > 40:
        lines = lines[:40] + [f"... [{len(lines) - 40} more lines truncated]"]

    return lines


# ─────────────────────────────────────────────────────────────────────────────

class Clause111Report:
    """Generates the full TCAF Word report for ITSAR clause 1.1.1."""

    def __init__(self, context, results):
        self._ctx    = context
        self.results = list(results)
        self.spec    = load_clause_spec(self._ctx_get("clause", "1.1.1"))

        self.output_dir = (
            self._ctx_get("run_dir")
            or getattr(self._ctx_get("evidence", None), "run_dir", None)
            or "output"
        )

        # ── DUT metadata ──────────────────────────────────────────────────
        raw_info = self._ctx_get("dut_info") or {}
        di = raw_info if isinstance(raw_info, dict) else vars(raw_info)

        self.meta = {
            "dut_name":    (di.get("dut_name")
                            or self._ctx_get("dut_name")
                            or self._ctx_get("dut_model", "Device Under Test")),
            "dut_version": (di.get("dut_version")
                            or self._ctx_get("dut_version")
                            or self._ctx_get("dut_firmware", "N/A")),
            "os_hash":       di.get("os_hash",     "N/A"),
            "config_hash":   di.get("config_hash", "N/A"),
            "start_time":    self._ctx_get("start_time", "N/A"),
            "end_time":      self._ctx_get("end_time",   "N/A"),
            "itsar_id":      self._ctx_get("itsar_section", "1.1.1"),
            "itsar_version": "1.0.1",
        }

        # ── Build runner_name → canonical_name lookup from YAML ───────────
        # Allows matching TC3_SSH_INVALID_CREDENTIALS → TC3_MUTUAL_AUTHENTICATION_SSH
        tc_specs = self.spec.get("testcases", {})
        self._runner_to_canonical: dict[str, str] = {}
        self._canonical_ordered: list[str] = list(tc_specs.keys())

        for canonical, tc_spec in tc_specs.items():
            runner_name = tc_spec.get("runner_name")
            if runner_name:
                self._runner_to_canonical[runner_name] = canonical
            # Also map canonical → itself so direct matches always work
            self._runner_to_canonical[canonical] = canonical

        # Position-based fallback: TC3 (index 2 in results) → 3rd YAML entry
        # Used when neither direct nor runner_name match succeeds.
        self._canonical_by_position = self._canonical_ordered

        # ── Merge results — handle duplicate TC names ──────────────────────
        # Duplicate TC names (e.g. TC8 appearing twice) are merged:
        #   • all evidence blocks are concatenated
        #   • last status wins (pessimistic — if either sub-check fails, FAIL)
        #
        # We also resolve runner names to canonical names here so all later
        # code works exclusively with canonical names.

        self._result_map: dict[str, dict] = {}   # canonical_name → merged result
        self._ran_canonical: list[str] = []       # ordered, deduped

        for pos, r in enumerate(self.results):
            runner_name = _get(r, "name", f"TC{pos+1}")
            canonical   = self._resolve_canonical(runner_name, pos)

            ev_existing = (self._result_map[canonical]["evidence"]
                           if canonical in self._result_map else [])
            ev_new      = _get(r, "evidence", []) or []

            if canonical in self._result_map:
                # Merge: append evidence, pessimistic status
                self._result_map[canonical]["evidence"] = ev_existing + ev_new
                new_status = _get(r, "status", "FAIL").upper()
                if new_status == "FAIL":
                    self._result_map[canonical]["status"] = "FAIL"
                # Keep original description (first occurrence)
            else:
                self._result_map[canonical] = {
                    "name":        canonical,
                    "description": _get(r, "description", ""),
                    "status":      _get(r, "status", "FAIL").upper(),
                    "evidence":    list(ev_new),
                }
                self._ran_canonical.append(canonical)

        # ── Counters ──────────────────────────────────────────────────────
        ran_set                = set(self._ran_canonical) & set(self._canonical_ordered)
        self._ran_count        = len(self._ran_canonical)
        self._total_defined    = len(self._canonical_ordered)
        self._not_run_count    = len(set(self._canonical_ordered) - ran_set)

        statuses = [self._result_map[n]["status"] for n in self._ran_canonical]
        self._pass_count = statuses.count("PASS")
        self._fail_count = len(statuses) - self._pass_count

        # PASS only when every defined case ran and all passed
        self.final_result = (
            "PASS"
            if self._fail_count == 0 and self._not_run_count == 0
            else "FAIL"
        )
        self.meta["final_result"] = self.final_result

    def _ctx_get(self, key, default=None):
        if isinstance(self._ctx, dict):
            return self._ctx.get(key, default)
        return getattr(self._ctx, key, default)

    def _resolve_canonical(self, runner_name: str, position: int) -> str:
        """
        Resolve a runner TC name to the canonical YAML name.

        Priority:
          1. Exact match on canonical name         TC1_MUTUAL_AUTHENTICATION
          2. runner_name field in spec             TC3_SSH_INVALID_CREDENTIALS
          3. Position fallback                     3rd result → 3rd YAML entry
        """
        if runner_name in self._runner_to_canonical:
            return self._runner_to_canonical[runner_name]
        # Position fallback
        if position < len(self._canonical_by_position):
            return self._canonical_by_position[position]
        # Unknown — use the runner name as-is (will show as NOT in spec)
        return runner_name

    # ── Section renderers ──────────────────────────────────────────────────

    def _section_revision_history(self, doc):
        section_heading(doc, "Revision History")
        two_col_info_table(doc,
            headers    = ["Version", "Date",                   "Changes"],
            col_widths = [1200,       1800,                     6360],
            data_rows  = [
                ("V.1.0", "Initial Release",
                 "NCCS Approved Test Plan with initial Test Cases."),
                ("V.1.1", self.meta["start_time"],
                 "First Release of Test Report — automated evidence collected."),
            ],
        )

    def _section_preface(self, doc):
        section_heading(doc, (
            "TSTR for Evaluation of 1.1 Management Protocols Entity "
            "Mutual Authentication (1.1.1 of CSR)"
        ))
        sub_heading(doc, "Preface")
        label_value_para(doc, "DUT Details", self.meta["dut_name"])
        spacer(doc)

        body_para(doc, "DUT Software Version:", bold=True)
        two_col_info_table(doc,
            headers    = ["Software Name",       "Software Version"],
            col_widths = [3600,                   5760],
            data_rows  = [("Device Firmware / OS", self.meta["dut_version"])],
        )
        spacer(doc)

        body_para(doc, "Digest Hash of OS:", bold=True)
        two_col_info_table(doc,
            headers    = ["Software Version",    "Hash Integrity Value"],
            col_widths = [3600,                   5760],
            data_rows  = [
                (self.meta["dut_version"], self.meta["os_hash"]),
                ("sshd_config",            self.meta["config_hash"]),
            ],
        )
        spacer(doc)

        body_para(doc, "Applicable ITSAR:", bold=True)
        for entry in self.spec["itsar"]["applicable_itsar"]:
            bullet_item(doc, f"{entry['ref']} ({entry['id']})")

        spacer(doc)
        body_para(doc, "ITSAR Version No.:", bold=True)
        for entry in self.spec["itsar"]["applicable_itsar"]:
            bullet_item(doc,
                f"{entry['version']} (Date of Release: {entry['release_date']})")

    def _section_requirement(self, doc):
        spacer(doc, large=True)
        itsar = self.spec["itsar"]
        body_para(doc,
            f"1. ITSAR Section No. & Name:  "
            f"{itsar['section_no']} {itsar['section_name']}",
            bold=True, color=PURPLE)
        body_para(doc,
            f"2. Security Requirement No. & Name:  "
            f"{itsar['requirement_no']} {itsar['requirement_name']}",
            bold=True, color=PURPLE)
        body_para(doc, "3. Requirement Description:", bold=True, color=PURPLE)
        body_para(doc, self.spec["requirement_description"].strip())

    def _section_dut_config(self, doc):
        spacer(doc, large=True)
        body_para(doc, "4. DUT Configuration:", bold=True, color=PURPLE)
        body_para(doc, "Note: " + self.spec["dut_config"]["split_mode_note"].strip())
        spacer(doc)
        body_para(doc, "1) OAM Access supported by DUT:", bold=True)
        two_col_info_table(doc,
            headers    = ["Protocol",  "Supported"],
            col_widths = [2800,         6560],
            data_rows  = [
                (row["protocol"], row["supported"])
                for row in self.spec["dut_config"]["oam_access"]
            ],
        )
        spacer(doc)
        body_para(doc, "NOTE:", bold=True, color=FAIL_RED)
        body_para(doc, self.spec["dut_config"]["snmp_note"].strip())

    def _section_preconditions(self, doc):
        spacer(doc, large=True)
        body_para(doc, "5. Pre-conditions:", bold=True, color=PURPLE)
        for cond in self.spec["preconditions"]:
            bullet_item(doc, cond)

    def _section_test_objective(self, doc):
        spacer(doc, large=True)
        body_para(doc, "6. Test Objective:", bold=True, color=PURPLE)
        bullet_item(doc, self.spec["test_objective"].strip())

    def _section_test_plan(self, doc):
        spacer(doc, large=True)
        body_para(doc, "7. Test Plan:", bold=True, color=PURPLE)
        bullet_item(doc, self.spec["test_plan"]["scope_note"].strip())
        spacer(doc)

        sub_heading(doc, "a. Number of Test Scenarios:")
        for idx, (_, tc) in enumerate(self.spec["testcases"].items(), start=1):
            numbered_item(doc, f"Test case {idx}: {tc['scenario']}")

        spacer(doc)
        sub_heading(doc, "b. Tools Required:")
        for tool in self.spec["test_plan"]["tools"]:
            bullet_item(doc, tool)

        spacer(doc)
        body_para(doc, "8. Expected Results for Pass:", bold=True, color=PURPLE)
        for idx, (_, tc) in enumerate(self.spec["testcases"].items(), start=1):
            numbered_item(doc, f"Test case {idx}: {tc['expected_result']}")

        spacer(doc)
        body_para(doc, "9. Expected Format of Evidence:", bold=True, color=PURPLE)
        body_para(doc, self.spec["test_plan"]["evidence_format"].strip())

    def _section_test_execution(self, doc):
        doc.add_page_break()
        section_heading(doc, "10. Test Execution")

        if self._not_run_count > 0:
            spacer(doc, small=True)
            body_para(
                doc,
                f"NOTE: This report covers {self._ran_count} of "
                f"{self._total_defined} defined test cases. "
                f"{self._not_run_count} case(s) were not executed in this run.",
                bold=True, color=FAIL_RED,
            )

        tc_specs = self.spec.get("testcases", {})

        # Render in run order, using merged results
        for idx, canonical in enumerate(self._ran_canonical, start=1):
            result = self._result_map[canonical]
            spec   = tc_specs.get(canonical, {})

            spacer(doc)
            tc_heading(doc, f"{idx}. Test Case Name: {canonical}")
            spacer(doc, small=True)

            # a. Description — YAML wins; fall back to runner description
            sub_heading(doc, "a. Test Case Description:")
            desc = (spec.get("description") or result.get("description") or "").strip()
            body_para(doc, desc or "No description available.")
            spacer(doc)

            # b. Execution steps (from YAML only — runner always sends [])
            steps = spec.get("steps", [])
            if steps:
                sub_heading(doc, "b. Execution Steps:")
                for step in steps:
                    numbered_item(doc, step)
                spacer(doc)

            # c. Evidence
            evidence = result.get("evidence", []) or []
            has_ev   = any(
                ev.get("command") or ev.get("output") or ev.get("screenshot")
                for ev in evidence
            )
            if has_ev:
                sub_heading(doc, "c. Evidence Captured:")
                for ev in evidence:
                    command    = ev.get("command")
                    output_raw = ev.get("output")
                    screenshot = ev.get("screenshot")

                    if command:
                        label_value_para(doc, "Command Executed", command)

                    if output_raw:
                        lines = _clean_terminal_output(output_raw)
                        if lines:
                            body_para(doc, "Command Output:", bold=True)
                            terminal_block(doc, lines)
                            spacer(doc, small=True)

                    if screenshot:
                        # add_screenshot handles broken object-repr paths
                        # internally via _resolve_screenshot_path
                        from icaf.reporting.helpers import _resolve_screenshot_path
                        clean = _resolve_screenshot_path(screenshot)
                        if clean:
                            body_para(
                                doc,
                                f"Evidence Screenshot — {os.path.basename(clean)}",
                                bold=True,
                            )
                            add_screenshot(doc, clean, width_inches=5.5)
                            spacer(doc, small=True)
                        else:
                            # Screenshot path recorded but file not accessible
                            # (common when object repr is in the path) — note it
                            fname = screenshot.split("/")[-1] if screenshot else ""
                            body_para(
                                doc,
                                f"Screenshot captured: {fname} "
                                f"(file path recorded; attach manually if required)",
                                italic=True, color=MID_GREY,
                            )

                spacer(doc)

            # d. Observations
            sub_heading(doc, "d. Test Observations:")
            obs = spec.get("observation", "").strip()
            body_para(doc, obs or "Observation recorded during test execution.")
            spacer(doc, small=True)

            # e. Evidence statement
            sub_heading(doc, "e. Evidence Provided:")
            body_para(doc,
                "Screenshots and command outputs are captured and attached "
                "during testing. Automated evidence is embedded above."
            )
            spacer(doc, small=True)

            # Result badge
            status_result_table(doc, result["status"])

            spacer(doc, large=True)
            _add_divider(doc)
            spacer(doc, large=True)

    def _section_result_summary(self, doc):
        doc.add_page_break()
        section_heading(doc, "11. Test Case Result Summary")
        spacer(doc)

        tc_specs   = self.spec.get("testcases", {})
        headers    = ["SL No.", "Test Case Name", "Result", "Remarks"]
        col_widths = [720, 3840, 1200, 3600]

        # All YAML-defined cases in spec order; NOT RUN for cases not executed
        data_rows = []
        for sl, canonical in enumerate(self._canonical_ordered, start=1):
            spec = tc_specs.get(canonical, {})
            if canonical in self._result_map:
                r       = self._result_map[canonical]
                status  = r["status"]
                remarks = spec.get("remarks", "")
            else:
                status  = "NOT RUN"
                remarks = "Test case was not executed in this run."
            data_rows.append((str(sl), canonical, status, remarks, status))

        totals_detail = (
            "All test cases passed successfully."
            if self.final_result == "PASS"
            else (
                f"{self._fail_count} case(s) failed"
                + (f", {self._not_run_count} not run." if self._not_run_count else ".")
            )
        )
        counts_str = f"{self._pass_count}P / {self._fail_count}F"
        if self._not_run_count:
            counts_str += f" / {self._not_run_count}NR"

        totals_row = (
            "",
            f"Total: {self._total_defined} defined  |  {self._ran_count} ran",
            counts_str,
            totals_detail,
            self.final_result,
        )
        _build_summary_table(doc, headers, col_widths, data_rows, totals_row)

    def _section_conclusion(self, doc):
        spacer(doc, large=True)
        section_heading(doc, "12. Test Conclusion")
        spacer(doc)

        for b in self.spec.get("conclusion_bullets", []):
            bullet_item(doc, b)

        if self._not_run_count > 0:
            bullet_item(
                doc,
                f"NOTE: This run executed {self._ran_count} of "
                f"{self._total_defined} defined test cases. The remaining "
                f"{self._not_run_count} case(s) were not run and must be "
                f"completed before a final pass verdict can be issued.",
                bold=True,
            )

        spacer(doc)
        status_result_table(
            doc,
            status=self.final_result,
            label="Overall Evaluation Result",
            detail=(
                f"{self._pass_count} of {self._total_defined} cases passed."
                if not self._not_run_count
                else f"{self._pass_count} passed, {self._fail_count} failed, "
                     f"{self._not_run_count} not run."
            ),
            wide=True,
        )

    # ── Entry point ───────────────────────────────────────────────────────────

    def generate(self) -> str:
        """Build and save <run_dir>/tcaf_report.docx. Returns the path."""
        os.makedirs(self.output_dir, exist_ok=True)
        report_path = os.path.join(self.output_dir, "tcaf_report.docx")

        doc = build_doc_with_header_footer(
            dut_name    = self.meta["dut_name"],
            dut_version = self.meta["dut_version"],
        )

        build_front_page(doc, self.meta)
        doc.add_page_break()

        self._section_revision_history(doc)
        doc.add_page_break()

        self._section_preface(doc)
        self._section_requirement(doc)
        self._section_dut_config(doc)
        self._section_preconditions(doc)
        self._section_test_objective(doc)
        self._section_test_plan(doc)

        self._section_test_execution(doc)
        self._section_result_summary(doc)
        self._section_conclusion(doc)

        doc.save(report_path)
        return report_path


# ── Module-private helpers ────────────────────────────────────────────────────

def _add_divider(doc):
    """Thin grey horizontal rule between test case blocks."""
    p    = doc.add_paragraph()
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "4")
    bot.set(qn("w:color"), "DDDDDD")
    pBdr.append(bot); pPr.append(pBdr)


def _build_summary_table(doc, headers, col_widths, data_rows, totals_row):
    """
    Result summary table.

    data_rows   list of 5-tuples:
                  (sl_str, canonical_name, status_text, remarks, status_key)
                  status_key  →  "PASS" | "FAIL" | "NOT RUN"

    totals_row  5-tuple:
                  (sl_empty, summary_str, counts_str, remark_str, final_key)
    """
    from docx.enum.table import WD_TABLE_ALIGNMENT

    table = doc.add_table(rows=0, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    _set_table_width(table, sum(col_widths))
    _set_col_widths(table, col_widths)

    # Header row
    hdr = table.add_row()
    for ci, (h, w) in enumerate(zip(headers, col_widths)):
        c = hdr.cells[ci]
        _style_cell(c, TABLE_HEADER_BG, HEX_PURPLE, w)
        _para_in_cell(c, h, bold=True, color=WHITE, center=True)

    # Data rows
    for ri, (sl, tc_name, status_text, remarks, status_key) in enumerate(data_rows):
        row    = table.add_row()
        row_bg = TABLE_ALT_BG if ri % 2 else "FFFFFF"
        sk     = status_key.upper()

        if sk == "PASS":
            s_bg = "E8F5E9"; s_col = RGBColor(0x00, 0x64, 0x00)
        elif sk == "NOT RUN":
            s_bg = NOT_RUN_BG; s_col = NOT_RUN_COLOR
        else:   # FAIL
            s_bg = "FFEBEE"; s_col = RGBColor(0xCC, 0x00, 0x00)

        for ci, (val, w) in enumerate(
            zip([sl, tc_name, status_text, remarks], col_widths)
        ):
            c = row.cells[ci]
            if ci == 2:   # status column
                _style_cell(c, s_bg, "CCCCCC", w)
                _para_in_cell(c, val, bold=True, color=s_col, center=True)
            else:
                _style_cell(c, row_bg, "CCCCCC", w)
                _para_in_cell(c, val, color=DARK_GREY, center=(ci == 0))

    # Totals row
    tot     = table.add_row()
    fk      = totals_row[4].upper()
    tot_col = (RGBColor(0x00, 0x64, 0x00) if fk == "PASS"
               else RGBColor(0xCC, 0x00, 0x00))
    for ci, (val, w) in enumerate(zip(totals_row[:4], col_widths)):
        c = tot.cells[ci]
        _style_cell(c, LIGHT_PURPLE, "CCCCCC", w)
        _para_in_cell(c, val, bold=True, color=tot_col, center=(ci in (0, 2)))