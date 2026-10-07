#!/usr/bin/env python3
"""
MASTER ORCHESTRATOR v3
Главный агент, который координирует работу всей команды
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class Orchestrator:
    def __init__(self, project_name: str, output_dir: str):
        self.project_name = project_name
        self.output_dir = Path(output_dir)
        self.agents_dir = Path("agents")
        self.logs = []
        
    def log(self, message: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{status}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def run_agent(self, agent_name: str, args: list) -> bool:
        """Запускает агента и возвращает True если успешно"""
        agent_script = self.agents_dir / f"{agent_name}.py"
        
        if not agent_script.exists():
            self.log(f"Агент {agent_name} не найден!", "ERROR")
            return False
        
        self.log(f"Запуск агента: {agent_name}", "START")
        
        try:
            cmd = [sys.executable, str(agent_script)] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"Агент {agent_name} завершён успешно", "SUCCESS")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log(f"Агент {agent_name} завершился с ошибкой: {result.stderr}", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            self.log(f"Агент {agent_name} превысил время выполнения (5 мин)", "ERROR")
            return False
        except Exception as e:
            self.log(f"Агент {agent_name} упал: {str(e)}", "ERROR")
            return False
    
    def generate_site(self):
        """Полный pipeline генерации сайта"""
        self.log("="*70)
        self.log(f"НАЧАЛО ГЕНЕРАЦИИ САЙТА: {self.project_name}")
        self.log("="*70)
        
        # Шаг 1: Site Planner
        self.log("ШАГ 1/5: Планирование структуры сайта")
        if not self.run_agent("site_planner", [
            "--project", self.project_name,
            "--output", str(self.output_dir)
        ]):
            self.log("Критическая ошибка на шаге 1. Остановка.", "FATAL")
            return False
        
        # Шаг 2: Design Agent
        self.log("ШАГ 2/5: Генерация дизайн-системы")
        if not self.run_agent("design_agent", [
            "--output", str(self.output_dir / "styles.css")
        ]):
            self.log("Критическая ошибка на шаге 2. Остановка.", "FATAL")
            return False
        
        # Шаг 3: Content Writer
        self.log("ШАГ 3/5: Генерация контента")
        if not self.run_agent("writer_v2_2", [
            "--site-map", str(self.output_dir / "site_map.json"),
            "--output-dir", str(self.output_dir),
            "--css-file", str(self.output_dir / "styles.css")
        ]):
            self.log("Критическая ошибка на шаге 3. Остановка.", "FATAL")
            return False
        
        # Шаг 4: QA Validator
        self.log("ШАГ 4/5: Проверка качества")
        if not self.run_agent("qa_validator", [
            "--site-dir", str(self.output_dir)
        ]):
            self.log("Предупреждение: QA обнаружил проблемы, но продолжаем", "WARNING")
        
        # Шаг 5: Deploy Agent
        self.log("ШАГ 5/5: Деплой на GitHub")
        if not self.run_agent("deploy_agent", [
            "--site-dir", str(self.output_dir),
            "--project-name", self.project_name
        ]):
            self.log("Ошибка деплоя, но сайт сгенерирован локально", "WARNING")
        
        self.log("="*70)
        self.log("ГЕНЕРАЦИЯ ЗАВЕРШЕНА")
        self.log("="*70)
        
        # Сохраняем логи
        log_file = self.output_dir / "orchestrator_log.txt"
        log_file.write_text("\n".join(self.logs), encoding="utf-8")
        self.log(f"Логи сохранены: {log_file}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Master Orchestrator v3")
    parser.add_argument("--project", required=True, help="Название проекта")
    parser.add_argument("--output", required=True, help="Директория вывода")
    args = parser.parse_args()
    
    orchestrator = Orchestrator(args.project, args.output)
    success = orchestrator.generate_site()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
