import os
import re
import shutil
from pathlib import Path

print("🚀 Запуск автономного исправления сайта...")

# 1. Читаем CSS
css_file = Path("styles.css")
if not css_file.exists():
    print("❌ Ошибка: файл styles.css не найден в текущей папке!")
    exit(1)

css_content = css_file.read_text(encoding="utf-8")
print(f"✅ CSS загружен ({len(css_content)} символов)")

# 2. JavaScript для интерактивности (FAQ + мобильное меню)
js_code = """
    <script>
        // FAQ Accordion
        document.querySelectorAll('.faq-question').forEach(question => {
            question.addEventListener('click', () => {
                const item = question.parentElement;
                const isActive = item.classList.contains('active');
                document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));
                if (!isActive) item.classList.add('active');
            });
        });
        // Mobile menu
        const burger = document.querySelector('.nav-burger');
        const mobileMenu = document.querySelector('.mobile-menu');
        const overlay = document.querySelector('.mobile-menu-overlay');
        if(burger) {
            burger.addEventListener('click', () => {
                burger.classList.toggle('active');
                mobileMenu.classList.toggle('active');
                overlay.classList.toggle('active');
            });
            overlay.addEventListener('click', () => {
                burger.classList.remove('active');
                mobileMenu.classList.remove('active');
                overlay.classList.remove('active');
            });
        }
        document.querySelectorAll('.mobile-parent').forEach(parent => {
            parent.addEventListener('click', (e) => {
                e.preventDefault();
                parent.parentElement.classList.toggle('open');
            });
        });
    </script>
"""

# 3. Находим все HTML файлы
site_dir = Path("data/sites/достойный_уход")
html_files = list(site_dir.rglob("index.html"))
print(f"🔍 Найдено HTML-файлов: {len(html_files)}")

fixed_count = 0
for html_file in html_files:
    content = html_file.read_text(encoding="utf-8")
    
    # Удаляем старые ссылки на внешний CSS (если есть)
    content = re.sub(r'<link[^>]*href=["\'][^"\']*styles\.css["\'][^>]*>', '', content)
    
    # Встраиваем CSS в <head>
    if '<style>' not in content:
        content = content.replace('</head>', f'    <style>\n{css_content}\n    </style>\n</head>')
    
    # Встраиваем JS перед </body>
    if '</script>' not in content or 'FAQ Accordion' not in content:
        content = content.replace('</body>', f'{js_code}\n</body>')
    
    html_file.write_text(content, encoding="utf-8")
    fixed_count += 1

print(f"✅ Успешно обновлено {fixed_count} файлов!")

# 4. Создаём ZIP архив
zip_name = "dostoinyy_ukhod_deploy"
if Path(f"{zip_name}.zip").exists():
    Path(f"{zip_name}.zip").unlink()

shutil.make_archive(zip_name, 'zip', site_dir)
final_size = Path(f"{zip_name}.zip").stat().st_size / 1024
print(f"📦 Архив создан: {zip_name}.zip ({final_size:.1f} KB)")
print("🎉 ВСЁ ГОТОВО! Можешь писать Сеньору 'Готово' и отправлять файл программисту!")
