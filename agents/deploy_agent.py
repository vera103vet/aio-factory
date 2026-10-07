#!/usr/bin/env python3
"""
DEPLOY AGENT
Создаёт ZIP, загружает на GitHub, создаёт бэкапы
"""

import argparse
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class DeployAgent:
    def __init__(self, site_dir: str, project_name: str, github_repo: str):
        self.site_dir = Path(site_dir)
        self.project_name = project_name
        self.github_repo = github_repo
        self.backup_dir = Path("data/backups")
        
        print("="*70)
        print("DEPLOY AGENT: Деплой сайта")
        print("="*70)
        print(f"📁 Директория: {self.site_dir}")
        print(f"📦 Проект: {self.project_name}")
        print(f"🌐 GitHub: {self.github_repo}")
        print("="*70)
    
    def create_zip(self) -> Path:
        """Создаёт ZIP-архив"""
        print("\n📦 Шаг 1: Создание ZIP-архива...")
        
        zip_name = f"{self.project_name}_deploy"
        zip_path = Path(f"{zip_name}.zip")
        
        if zip_path.exists():
            zip_path.unlink()
        
        shutil.make_archive(zip_name, 'zip', self.site_dir)
        
        size_kb = zip_path.stat().st_size / 1024
        print(f"✅ Архив создан: {zip_path} ({size_kb:.1f} KB)")
        
        return zip_path
    
    def create_backup(self) -> Path:
        """Создаёт бэкап с датой"""
        print("\n💾 Шаг 2: Создание бэкапа...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backup_{self.project_name}_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        shutil.make_archive(str(backup_path), 'zip', self.site_dir)
        
        print(f"✅ Бэкап создан: {backup_path}")
        
        return backup_path
    
    def upload_to_github(self, zip_path: Path) -> bool:
        """Загружает на GitHub"""
        print("\n🌐 Шаг 3: Загрузка на GitHub...")
        
        try:
            # Проверяем, есть ли git
            result = subprocess.run(
                ["git", "status"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("⚠️  Git не инициализирован. Пропускаем загрузку.")
                return False
            
            # Добавляем файл
            subprocess.run(["git", "add", str(zip_path)], check=True)
            
            # Коммит
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(
                ["git", "commit", "-m", f"Deploy {self.project_name}: {timestamp}"],
                check=True
            )
            
            # Push
            subprocess.run(["git", "push"], check=True)
            
            print(f"✅ Загружено на GitHub: {self.github_repo}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False
    
    def run(self):
        """Запускает полный деплой"""
        # Шаг 1: ZIP
        zip_path = self.create_zip()
        
        # Шаг 2: Бэкап
        backup_path = self.create_backup()
        
        # Шаг 3: GitHub
        github_success = self.upload_to_github(zip_path)
        
        # Итог
        print("\n" + "="*70)
        print("ИТОГОВЫЙ ОТЧЁТ")
        print("="*70)
        print(f"📦 Архив: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
        print(f"💾 Бэкап: {backup_path}")
        print(f"🌐 GitHub: {'✅ Загружено' if github_success else '⚠️  Пропущено'}")
        print("="*70)
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Deploy Agent")
    parser.add_argument("--site-dir", required=True, help="Директория сайта")
    parser.add_argument("--project-name", required=True, help="Название проекта")
    parser.add_argument("--github-repo", required=True, help="GitHub репозиторий")
    args = parser.parse_args()
    
    agent = DeployAgent(args.site_dir, args.project_name, args.github_repo)
    success = agent.run()
    
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
