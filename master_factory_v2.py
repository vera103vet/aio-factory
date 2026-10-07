#!/usr/bin/env python3
"""
MASTER FACTORY v2.0 - Двухэтапная архитектура (Вариант C)
Этап 1: Постраничная генерация (Writer -> Editor -> Critic)
Этап 2: Пакетная оптимизация (Linker -> SEO)
Этап 3: Параллельный аудит
"""

import json
import sys
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class MasterFactoryV2:
    def __init__(self, project_name: str, num_pages: int, styles_file: str, starter_file: str, test_mode: bool = False):
        self.project_name = project_name
        self.num_pages = min(num_pages, 5) if test_mode else num_pages
        self.styles_file = Path(styles_file)
        self.starter_file = Path(starter_file)
        self.project_dir = Path(f"data/sites/{project_name}")
        self.agents_dir = Path("agents")
        self.log_file = self.project_dir / "factory_v2.log"
        
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        self.log("=" * 70)
        self.log("🏭 MASTER FACTORY v2.0 (Двухэтапная архитектура)")
        self.log("=" * 70)
        self.log(f"Проект: {project_name}")
        self.log(f"Страниц: {self.num_pages} {'(ТЕСТ)' if test_mode else ''}")
        self.log("=" * 70)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def run_cmd(self, cmd: str, timeout: int = 60) -> bool:
        """Запускает команду и возвращает True при успехе (код 0)"""
        self.log(f"  ▶️  {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                self.log("  ✅ Успешно")
                return True
            else:
                self.log(f"  ❌ Ошибка (код {result.returncode}): {result.stderr[:200]}")
                return False
        except subprocess.TimeoutExpired:
            self.log(f"  ⏱️  Таймаут ({timeout}с)")
            return False
        except Exception as e:
            self.log(f"  ❌ Исключение: {e}")
            return False

    def generate_and_validate_page(self, page_id: int, topic: str) -> bool:
        """Этап 1: Генерация и постраничная валидация"""
        self.log(f"\nСтраница {page_id}: {topic}")
        
        html_file = self.project_dir / f"page-{page_id}.html"
        
        # 1. Writer (через адаптер)
        self.log("  [1/3] Генерация контента (Writer v2.2)...")
        temp_input = self.project_dir / f"temp_input_w.json"
        with open(temp_input, "w", encoding="utf-8") as f:
            json.dump({"page_id": page_id, "topic": topic, "html_content": ""}, f, ensure_ascii=False)
        
        cmd_w = f"python3 adapter_writer_v2_2.py --input {temp_input} --project {self.project_name}"
        if not self.run_cmd(cmd_w, timeout=120):
            return False
        
        # Проверяем, создал ли адаптер файл
        output_files = list((self.project_dir / "writer_output").rglob("*.html"))
        if not output_files:
            self.log("  Writer не создал HTML файл")
            return False
        
        shutil.copy(output_files[0], html_file)
        self.log(f"  HTML сохранён: {html_file.name}")
        
        # 2. Chief Editor
        self.log("  [2/3] Редактура (Chief Editor v1.1)...")
        cmd_e = f"python3 {self.agents_dir}/chief_editor_v1_1.py --file {html_file}"
        if not self.run_cmd(cmd_e, timeout=60):
            self.log("  Editor завершил с предупреждениями, продолжаем")
        
        # 3. Domain Expert Critic
        self.log("  [3/3] Фактчекинг (Critic v2.1)...")
        cmd_c = f"python3 {self.agents_dir}/domain_expert_critic_v2_1.py --file {html_file}"
        if not self.run_cmd(cmd_c, timeout=60):
            self.log("  Critic завершил с предупреждениями, продолжаем")
            
        return True

    def run_batch_optimization(self) -> bool:
        """Этап 2: Пакетная оптимизация всего проекта"""
        self.log("\n" + "=" * 70)
        self.log("ЭТАП 2: Пакетная оптимизация сайта")
        self.log("=" * 70)
        
        # 4. Linker AI v5
        self.log("  [4/5] Перелинковка (Linker AI v5)...")
        cmd_l = f"python3 {self.agents_dir}/linker_ai_v5.py"
        if not self.run_cmd(cmd_l, timeout=120):
            self.log("  Linker завершил с предупреждениями")
        
        # 5. URL SEO Specialist
        self.log("  [5/5] SEO оптимизация (URL SEO Specialist)...")
        cmd_s = f"python3 {self.agents_dir}/url_seo_specialist.py"
        if not self.run_cmd(cmd_s, timeout=120):
            self.log("  SEO завершил с предупреждениями")
            
        return True

    def run_parallel_audit(self) -> dict:
        """Этап 3: Параллельный аудит итоговых файлов"""
        self.log("\n" + "=" * 70)
        self.log("ЭТАП 3: Параллельный аудит (12 аудиторов)")
        self.log("=" * 70)
        
        auditor_ids = [
            "auditor_ymyl", "auditor_ethics", "auditor_accessibility",
            "auditor_schema_geo", "auditor_links", "auditor_html_tech",
            "auditor_mobile", "auditor_antifluff", "auditor_ux_conversion",
            "auditor_contacts", "auditor_security", "auditor_brand"
        ]
        
        approved_count = 0
        html_files = list(self.project_dir.glob("*.html"))
        first_html = str(html_files[0]) if html_files else ""
        
        def run_auditor(auditor_id: str) -> bool:
            if first_html:
                cmd = f"python3 {self.agents_dir}/{auditor_id}.py --file {first_html}"
            else:
                cmd = f"python3 {self.agents_dir}/{auditor_id}.py"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(run_auditor, aid): aid for aid in auditor_ids}
            for future in as_completed(futures):
                aid = futures[future]
                try:
                    if future.result():
                        approved_count += 1
                        self.log(f"  OK: {aid}")
                    else:
                        self.log(f"  FAIL: {aid}")
                except Exception as e:
                    self.log(f"  WARN: {aid} ({e})")
                    
        self.log(f"\nИтог аудита: {approved_count}/{len(auditor_ids)} одобрено")
        return {"approved": approved_count, "total": len(auditor_ids)}

    def run(self) -> bool:
        """Запуск полного конвейера"""
        start_time = time.time()
        
        # Копируем стили
        if self.styles_file.exists():
            shutil.copy(self.styles_file, self.project_dir / "styles.css")
        
        self.log(f"\nНачинаем генерацию {self.num_pages} страниц...")
        
        # ЭТАП 1: Постраничная генерация
        success_pages = 0
        for page_id in range(1, self.num_pages + 1):
            topic = f"Тестовая страница {page_id} - Ветеринарная помощь"
            if self.generate_and_validate_page(page_id, topic):
                success_pages += 1
                
        if success_pages == 0:
            self.log("\nЭТАП 1 провален. Ни одна страница не создана.")
            return False
            
        self.log(f"\nЭТАП 1 завершён: {success_pages}/{self.num_pages} страниц создано.")
        
        # ЭТАП 2: Пакетная оптимизация
        self.run_batch_optimization()
        
        # ЭТАП 3: Параллельный аудит
        audit_result = self.run_parallel_audit()
        
        elapsed = time.time() - start_time
        
        self.log("\n" + "=" * 70)
        self.log("ИТОГОВЫЙ ОТЧЁТ")
        self.log("=" * 70)
        self.log(f"Создано страниц: {success_pages}")
        self.log(f"Аудит пройден: {audit_result['approved']}/{audit_result['total']}")
        self.log(f"Время выполнения: {elapsed:.1f} сек ({elapsed/60:.1f} мин)")
        self.log(f"Папка проекта: {self.project_dir.absolute()}")
        self.log("=" * 70)
        
        return audit_result['approved'] >= 10


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master Factory v2.0 (Двухэтапный)")
    parser.add_argument("--project", required=True, help="Название проекта")
    parser.add_argument("--pages", type=int, required=True, help="Количество страниц")
    parser.add_argument("--styles", required=True, help="Файл styles.css")
    parser.add_argument("--starter", required=True, help="Стартовый HTML-файл")
    parser.add_argument("--test", action="store_true", help="Тестовый режим (макс. 5 страниц)")
    
    args = parser.parse_args()
    
    factory = MasterFactoryV2(
        args.project, args.pages, args.styles, args.starter, test_mode=args.test
    )
    success = factory.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
