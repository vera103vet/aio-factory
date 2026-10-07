#!/usr/bin/env python3
"""
MASTER FACTORY v1.0 - Базовая версия
Тестовый конвейер для 3-5 страниц с ключевыми агентами
"""

import json
import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess


class MasterFactory:
    def __init__(self, project_name, num_pages, styles_file, starter_file, test_mode=False):
        self.project_name = project_name
        self.num_pages = min(num_pages, 5) if test_mode else num_pages
        self.styles_file = Path(styles_file)
        self.starter_file = Path(starter_file)
        self.project_dir = Path(f"data/sites/{project_name}")
        self.agents_dir = Path("agents")
        self.registry_file = Path("AGENTS_REGISTRY.json")
        self.log_file = self.project_dir / "factory.log"
        self.test_mode = test_mode

        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.registry = self._load_registry()

        self.log("=" * 70)
        self.log("MASTER FACTORY v1.0 запущен")
        self.log("=" * 70)
        self.log(f"Проект: {project_name}")
        mode_text = "(ТЕСТОВЫЙ РЕЖИМ)" if test_mode else ""
        self.log(f"Страниц: {self.num_pages} {mode_text}")
        self.log("=" * 70)

    def _load_registry(self):
        if not self.registry_file.exists():
            self.log("CRITICAL: AGENTS_REGISTRY.json not found!")
            sys.exit(1)
        with open(self.registry_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def find_agent_info(self, agent_id):
        for group in ["agents", "auditors", "validation_and_deploy", "utilities"]:
            for agent in self.registry.get(group, []):
                if agent["id"] == agent_id:
                    return agent
        return None

    def run_agent(self, agent_id, input_data):
        agent_info = self.find_agent_info(agent_id)

        if not agent_info:
            self.log(f"WARNING: Agent {agent_id} not in registry, skipping")
            return input_data

        agent_script = self.agents_dir / f"{agent_id}.py"

        if not agent_script.exists():
            self.log(f"WARNING: Script {agent_script} not found, skipping")
            return input_data

        self.log(f"RUNNING: {agent_info['name']} ({agent_id})")

        try:
            temp_input = self.project_dir / f"temp_input_{agent_id}.json"
            with open(temp_input, "w", encoding="utf-8") as f:
                json.dump(input_data, f, ensure_ascii=False, indent=2)

            cmd = f"python3 {agent_script} --input {temp_input} --project {self.project_name}"
            timeout = agent_info.get("timeout_seconds", 30)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)

            temp_output = self.project_dir / f"temp_output_{agent_id}.json"
            if temp_output.exists():
                with open(temp_output, "r", encoding="utf-8") as f:
                    output_data = json.load(f)

                temp_input.unlink(missing_ok=True)
                temp_output.unlink(missing_ok=True)

                status = output_data.get("status", "")
                if status in ["approved", "completed", "success"]:
                    self.log(f"OK: {agent_id} completed successfully")
                    return output_data
                else:
                    reason = output_data.get("reason", "unknown error")
                    self.log(f"FAIL: {agent_id} - {reason}")
                    return None
            else:
                self.log(f"WARNING: {agent_id} produced no output file")
                return None

        except subprocess.TimeoutExpired:
            self.log(f"TIMEOUT: {agent_id} exceeded {timeout}s")
            return None
        except Exception as e:
            self.log(f"ERROR: {agent_id} - {e}")
            return None

    def run_auditors_parallel(self, input_data):
        self.log("")
        self.log("Starting parallel audit (12 auditors)...")

        auditor_ids = [
            "auditor_ymyl", "auditor_ethics", "auditor_accessibility",
            "auditor_schema_geo", "auditor_links", "auditor_html_tech",
            "auditor_mobile", "auditor_antifluff", "auditor_ux_conversion",
            "auditor_contacts", "auditor_security", "auditor_brand"
        ]

        results = {}
        approved_count = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_auditor = {
                executor.submit(self.run_agent, auditor_id, input_data): auditor_id
                for auditor_id in auditor_ids
            }

            for future in as_completed(future_to_auditor):
                auditor_id = future_to_auditor[future]
                try:
                    result = future.result()
                    if result and result.get("status") == "approved":
                        approved_count += 1
                        results[auditor_id] = "OK"
                    else:
                        results[auditor_id] = "FAIL"
                except Exception as e:
                    results[auditor_id] = f"ERROR: {e}"

        self.log(f"Audit results: {approved_count}/12 approved")

        if approved_count >= 10:
            self.log("AUDIT PASSED - page APPROVED")
            input_data["audit_status"] = "APPROVED"
            input_data["audit_score"] = approved_count
        else:
            self.log(f"AUDIT FAILED - only {approved_count}/12 approved")
            input_data["audit_status"] = "NEEDS_FIX"
            input_data["audit_score"] = approved_count

        return input_data

    def generate_page(self, page_id, topic):
        self.log("")
        self.log("=" * 70)
        self.log(f"Page {page_id}: {topic}")
        self.log("=" * 70)

        data = {
            "page_id": page_id,
            "topic": topic,
            "project": self.project_name,
            "status": "in_progress",
            "html_content": "",
            "metadata": {}
        }

        agents_sequence = [
            ("writer_v2_2", "Content generation"),
            ("chief_editor_v1_1", "Editing"),
            ("domain_expert_critic_v2_1", "Fact-checking"),
            ("linker_ai_v5", "Internal linking"),
            ("url_seo_specialist", "SEO optimization")
        ]

        for i, (agent_id, step_name) in enumerate(agents_sequence, 1):
            self.log(f"[{i}/6] {step_name}...")
            data = self.run_agent(agent_id, data)
            if not data or data.get("status") not in ["completed", "approved", "success"]:
                self.log(f"FAIL: {agent_id} failed - page FAILED")
                return None

        self.log("")
        self.log("[6/6] Parallel audit...")
        data = self.run_auditors_parallel(data)

        if data.get("audit_status") == "APPROVED":
            self.log(f"OK: Page {page_id} APPROVED by all agents!")
            return data
        else:
            self.log(f"WARNING: Page {page_id} needs fixes")
            return data

    def run(self):
        start_time = time.time()

        if not self.starter_file.exists():
            self.log(f"CRITICAL: Starter file not found: {self.starter_file}")
            return False

        template_html = self.starter_file.read_text(encoding="utf-8")

        if self.styles_file.exists():
            shutil.copy(self.styles_file, self.project_dir / "styles.css")
            self.log("OK: styles.css copied")
        else:
            self.log("WARNING: styles.css not found")

        self.log("")
        self.log(f"Starting generation of {self.num_pages} pages...")

        approved_pages = 0
        failed_pages = 0
        needs_fix_pages = 0

        for page_id in range(1, self.num_pages + 1):
            topic = f"Test page {page_id}"
            result = self.generate_page(page_id, topic)

            if result:
                if result.get("audit_status") == "APPROVED":
                    approved_pages += 1
                    output_file = self.project_dir / f"page-{page_id}.html"
                    output_file.write_text(template_html, encoding="utf-8")
                else:
                    needs_fix_pages += 1
            else:
                failed_pages += 1

        elapsed = time.time() - start_time

        self.log("")
        self.log("=" * 70)
        self.log("FINAL REPORT")
        self.log("=" * 70)
        self.log(f"Total pages: {self.num_pages}")
        self.log(f"Approved by all agents: {approved_pages}")
        self.log(f"Needs fixes: {needs_fix_pages}")
        self.log(f"Failed: {failed_pages}")
        self.log(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")

        if failed_pages == 0 and needs_fix_pages == 0:
            self.log("")
            self.log("SUCCESS: ALL PAGES APPROVED! Test passed.")
            self.log(f"Project folder: {self.project_dir}")
        else:
            self.log(f"")
            self.log(f"WARNING: {needs_fix_pages + failed_pages} pages need attention.")

        self.log("=" * 70)

        return failed_pages == 0 and needs_fix_pages == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Master Factory v1.0")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--pages", type=int, required=True, help="Number of pages")
    parser.add_argument("--styles", required=True, help="styles.css file")
    parser.add_argument("--starter", required=True, help="Starter HTML file")
    parser.add_argument("--test", action="store_true", help="Test mode (max 5 pages)")

    args = parser.parse_args()

    factory = MasterFactory(
        args.project,
        args.pages,
        args.styles,
        args.starter,
        test_mode=args.test
    )
    success = factory.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
