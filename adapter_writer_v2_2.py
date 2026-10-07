#!/usr/bin/env python3
"""
Адаптер для writer_v2_2.py
Принимает формат master_factory.py (--input, --project)
Преобразует в формат writer_v2_2 (--site-map, --css, --output-dir)
"""

import json
import sys
import subprocess
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Adapter for writer_v2_2")
    parser.add_argument("--input", required=True, help="Input JSON from master_factory")
    parser.add_argument("--project", required=True, help="Project name")
    args = parser.parse_args()
    
    # Читаем входные данные от master_factory
    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)
    
    project_dir = Path(f"data/sites/{args.project}")
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаём site_map.json для writer_v2_2
    site_map = {
        "pages": [
            {
                "name": input_data.get("topic", "Test page"),
                "url": f"/page-{input_data.get('page_id', 1)}.html",
                "content": input_data.get("html_content", "")
            }
        ]
    }
    
    site_map_file = project_dir / f"site_map_{input_data.get('page_id', 1)}.json"
    with open(site_map_file, "w", encoding="utf-8") as f:
        json.dump(site_map, f, ensure_ascii=False, indent=2)
    
    # CSS файл
    css_file = Path("styles.css")
    
    # Output директория
    output_dir = project_dir / "writer_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Запускаем writer_v2_2 с правильными аргументами
    cmd = f"python3 agents/writer_v2_2.py --site-map {site_map_file} --css {css_file} --output-dir {output_dir}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Проверяем результат
    output_files = list(output_dir.glob("*.html"))
    
    if output_files:
        # Читаем первый созданный файл
        html_content = output_files[0].read_text(encoding="utf-8")
        
        # Создаём выходной JSON для master_factory
        output_data = {
            "page_id": input_data.get("page_id"),
            "status": "completed",
            "html_content": html_content,
            "metadata": {
                "writer_version": "v2.2",
                "output_file": str(output_files[0])
            }
        }
        
        output_file = project_dir / f"temp_output_writer_v2_2.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"OK: Created {len(output_files)} HTML files")
    else:
        # Ошибка
        output_data = {
            "page_id": input_data.get("page_id"),
            "status": "failed",
            "reason": f"writer_v2_2 produced no output. stderr: {result.stderr[:200]}"
        }
        
        output_file = project_dir / f"temp_output_writer_v2_2.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"FAIL: {output_data['reason']}")

if __name__ == "__main__":
    main()
