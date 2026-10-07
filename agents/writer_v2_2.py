#!/usr/bin/env python3
"""
WRITER AI PRO v2.2
Генератор HTML-страниц со встроенными стилями и JavaScript
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime

class WriterV22:
    def __init__(self, site_map_file: str, css_file: str, output_dir: str):
        self.site_map_file = Path(site_map_file)
        self.css_file = Path(css_file)
        self.output_dir = Path(output_dir)
        
        # Загружаем данные
        self.site_map = self.load_site_map()
        self.css_content = self.load_css()
        
        # JavaScript для интерактивности
        self.js_code = """
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
        
        // Mobile submenu toggle
        document.querySelectorAll('.mobile-parent').forEach(parent => {
            parent.addEventListener('click', (e) => {
                e.preventDefault();
                parent.parentElement.classList.toggle('open');
            });
        });
    </script>
"""
        
        print("="*70)
        print("WRITER AI PRO v2.2: Генерация HTML со встроенными стилями")
        print("="*70)
        print(f" Карта сайта: {self.site_map_file}")
        print(f"🎨 CSS файл: {self.css_file}")
        print(f" Вывод: {self.output_dir}")
        print(f"📊 Страниц: {len(self.site_map.get('pages', []))}")
        print("="*70)
    
    def load_site_map(self) -> dict:
        """Загружает карту сайта"""
        if not self.site_map_file.exists():
            raise FileNotFoundError(f"Карта сайта не найдена: {self.site_map_file}")
        
        with open(self.site_map_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_css(self) -> str:
        """Загружает CSS файл"""
        if not self.css_file.exists():
            raise FileNotFoundError(f"CSS файл не найден: {self.css_file}")
        
        return self.css_file.read_text(encoding="utf-8")
    
    def generate_navigation(self) -> str:
        """Генерирует навигационное меню"""
        return """
    <nav class="nav">
        <a href="/" class="nav-logo">103vet.by</a>
        <ul class="nav-menu">
            <li><a href="/">Главная</a></li>
            <li class="has-dropdown">
                <a href="/guide/">Руководства <span class="nav-arrow">▼</span></a>
                <div class="nav-dropdown">
                    <div class="dropdown-group">
                        <div class="dropdown-title">Поддержка собак</div>
                        <ul class="dropdown-list">
                            <li><a href="/how-to/podderzhka-sobak/onkologiya/">Онкология</a></li>
                            <li><a href="/how-to/podderzhka-sobak/paralichi/">Параличи</a></li>
                            <li><a href="/how-to/podderzhka-sobak/kontrol-boli/">Контроль боли</a></li>
                        </ul>
                    </div>
                    <div class="dropdown-group">
                        <div class="dropdown-title">Поддержка кошек</div>
                        <ul class="dropdown-list">
                            <li><a href="/how-to/podderzhka-koshek/gipertireoz/">Гипертиреоз</a></li>
                            <li><a href="/how-to/podderzhka-koshek/hbp/">ХПН</a></li>
                            <li><a href="/how-to/podderzhka-koshek/artrit/">Артрит</a></li>
                        </ul>
                    </div>
                </div>
                <div class="nav-dropdown-bridge"></div>
            </li>
            <li><a href="/blog/">Блог</a></li>
            <li><a href="/about/">О проекте</a></li>
            <li><a href="/contacts/">Контакты</a></li>
        </ul>
        <button class="nav-burger" aria-label="Открыть меню">
            <span></span><span></span><span></span>
        </button>
    </nav>

    <div class="mobile-menu-overlay"></div>
    <div class="mobile-menu">
        <ul class="mobile-menu-list">
            <li><a href="/">Главная</a></li>
            <li>
                <button class="mobile-parent">Руководства <span class="mobile-parent-arrow">▼</span></button>
                <div class="mobile-submenu">
                    <div class="mobile-submenu-inner">
                        <div class="dropdown-group">
                            <div class="dropdown-title">Поддержка собак</div>
                            <ul class="dropdown-list">
                                <li><a href="/how-to/podderzhka-sobak/onkologiya/">Онкология</a></li>
                                <li><a href="/how-to/podderzhka-sobak/paralichi/">Параличи</a></li>
                                <li><a href="/how-to/podderzhka-sobak/kontrol-boli/">Контроль боли</a></li>
                            </ul>
                        </div>
                        <div class="dropdown-group">
                            <div class="dropdown-title">Поддержка кошек</div>
                            <ul class="dropdown-list">
                                <li><a href="/how-to/podderzhka-koshek/gipertireoz/">Гипертиреоз</a></li>
                                <li><a href="/how-to/podderzhka-koshek/hbp/">ХПН</a></li>
                                <li><a href="/how-to/podderzhka-koshek/artrit/">Артрит</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            <li><a href="/blog/">Блог</a></li>
            <li><a href="/about/">О проекте</a></li>
            <li><a href="/contacts/">Контакты</a></li>
        </ul>
    </div>
"""
    
    def generate_footer(self) -> str:
        """Генерирует футер"""
        return """
    <footer>
        <div class="footer-content">
            <div class="footer-brand">
                <h3>103vet.by</h3>
                <p>Ветеринарная клиника. Профессиональная помощь вашим питомцам на каждом этапе жизни.</p>
            </div>
            <div class="footer-section">
                <h4>Навигация</h4>
                <ul>
                    <li><a href="/">Главная</a></li>
                    <li><a href="/guide/">Руководства</a></li>
                    <li><a href="/blog/">Блог</a></li>
                    <li><a href="/about/">О проекте</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>Направления</h4>
                <ul>
                    <li><a href="/how-to/podderzhka-sobak/">Собаки</a></li>
                    <li><a href="/how-to/podderzhka-koshek/">Кошки</a></li>
                    <li><a href="/guide/kak-oczenit-kachestvo-zhizni/">Качество жизни</a></li>
                    <li><a href="/guide/psixologicheskaya-pomoshch/">Помощь владельцу</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>Контакты</h4>
                <ul>
                    <li><a href="tel:+37529XXXXXXX">+375 (29) XXX-XX-XX</a></li>
                    <li>Минск и область</li>
                    <li>Круглосуточно</li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2026 103vet.by. Все права защищены.</p>
            <p><a href="/privacy/">Политика конфиденциальности</a> | <a href="/terms/">Условия использования</a></p>
        </div>
    </footer>
"""
    
    def generate_page_content(self, page: dict) -> str:
        """Генерирует контент страницы в зависимости от типа"""
        page_type = page.get("type", "article")
        page_name = page.get("name", "Страница")
        page_url = page.get("url", "/")
        
        if page_type == "home":
            return self.generate_home_page(page_name)
        elif page_type == "article":
            return self.generate_article_page(page_name, page_url)
        elif page_type == "legal":
            return self.generate_legal_page(page_name)
        else:
            return self.generate_generic_page(page_name)
    
    def generate_home_page(self, page_name: str) -> str:
        """Генерирует главную страницу"""
        return f"""
    <main>
        <section class="hero">
            <div class="hero-visual">
                <div class="glow glow-1"></div>
                <div class="glow glow-2"></div>
            </div>
            <div class="hero-content">
                <div class="hero-meta">
                    <span class="section-number">01</span>
                    <span>Ветеринарная паллиативная помощь</span>
                </div>
                <h1>Достойный уход за <em>вашим питомцем</em></h1>
                <p class="hero-subtitle">
                    Профессиональная поддержка на каждом этапе. Мы помогаем сохранить качество жизни вашего питомца и облегчить его состояние.
                </p>
                <div class="hero-cta">
                    <a href="/contacts/" class="btn btn-primary">Получить консультацию</a>
                    <a href="/guide/" class="btn btn-ghost">Читать руководства</a>
                </div>
            </div>
        </section>

        <section class="section philosophy">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">02</span>
                        <span>Наша философия</span>
                    </div>
                    <h2>Забота до последнего вздоха</h2>
                    <p>Мы верим, что каждый питомец заслуживает достойного ухода, независимо от стадии заболевания.</p>
                </div>
                <div class="philosophy-content">
                    <p class="philosophy-text">
                        Паллиативная помощь — это не отказ от лечения, а смена фокуса. Мы концентрируемся на качестве жизни, контроле боли и эмоциональной поддержке как питомца, так и его семьи.
                    </p>
                    <div class="philosophy-note">
                        <strong>Важно:</strong> Наши специалисты работают в тесном контакте с вашим лечащим ветеринаром, чтобы обеспечить непрерывность и согласованность ухода.
                    </div>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">03</span>
                        <span>Направления помощи</span>
                    </div>
                    <h2>Чем мы можем помочь</h2>
                    <p>Выберите направление, которое актуально для вашей ситуации</p>
                </div>
                <div class="directions-grid">
                    <a href="/how-to/podderzhka-sobak/" class="direction-card">
                        <div class="direction-number">01</div>
                        <h3>Поддержка собак</h3>
                        <p>Онкология, параличи, контроль боли, паллиативный уход при хронических заболеваниях.</p>
                        <div class="direction-link">Подробнее</div>
                    </a>
                    <a href="/how-to/podderzhka-koshek/" class="direction-card">
                        <div class="direction-number">02</div>
                        <h3>Поддержка кошек</h3>
                        <p>Гипертиреоз, хроническая почечная недостаточность, артрит, деменция.</p>
                        <div class="direction-link">Подробнее</div>
                    </a>
                    <a href="/guide/kak-oczenit-kachestvo-zhizni/" class="direction-card">
                        <div class="direction-number">03</div>
                        <h3>Качество жизни</h3>
                        <p>Шкалы оценки, дневники наблюдений, протоколы принятия сложных решений.</p>
                        <div class="direction-link">Подробнее</div>
                    </a>
                    <a href="/guide/psixologicheskaya-pomoshch/" class="direction-card">
                        <div class="direction-number">04</div>
                        <h3>Помощь владельцу</h3>
                        <p>Психологическая поддержка, работа с горем, помощь детям, группы поддержки.</p>
                        <div class="direction-link">Подробнее</div>
                    </a>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">04</span>
                        <span>Частые вопросы</span>
                    </div>
                    <h2>Ответы на важные вопросы</h2>
                </div>
                <div class="faq-list">
                    <div class="faq-item">
                        <div class="faq-question">
                            <span>Когда начинать паллиативный уход?</span>
                            <span class="faq-icon">+</span>
                        </div>
                        <div class="faq-answer">
                            <p>Паллиативный уход начинается тогда, когда лечение уже не может полностью вылечить заболевание, но ещё может улучшить качество жизни.</p>
                        </div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">
                            <span>Как понять, что питомцу больно?</span>
                            <span class="faq-icon">+</span>
                        </div>
                        <div class="faq-answer">
                            <p>Животные часто скрывают боль. Признаки: снижение активности, изменение аппетита, избегание прикосновений.</p>
                        </div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">
                            <span>Можно ли получать помощь на дому?</span>
                            <span class="faq-icon">+</span>
                        </div>
                        <div class="faq-answer">
                            <p>Да, мы предоставляем консультации и поддержку на дому.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section class="palliative">
            <div class="palliative-content">
                <div class="palliative-badge">Консультация специалиста</div>
                <h2>Нужна помощь прямо сейчас?</h2>
                <p>Наши специалисты готовы ответить на ваши вопросы и помочь составить план ухода за вашим питомцем.</p>
                <a href="tel:+37529XXXXXXX" class="btn btn-primary">📞 Получить консультацию</a>
            </div>
        </section>
    </main>
"""
    
    def generate_article_page(self, page_name: str, page_url: str) -> str:
        """Генерирует страницу статьи"""
        return f"""
    <main>
        <section class="section">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">01</span>
                        <span>Статья</span>
                    </div>
                    <h2>{page_name}</h2>
                </div>
                <div class="philosophy-content">
                    <p class="philosophy-text">
                        Контент для страницы "{page_name}" находится в разработке. 
                        Здесь будет размещена подробная информация по теме.
                    </p>
                    <div class="philosophy-note">
                        <strong>Важно:</strong> Эта страница будет дополнена экспертным контентом в ближайшее время.
                    </div>
                </div>
            </div>
        </section>
    </main>
"""
    
    def generate_legal_page(self, page_name: str) -> str:
        """Генерирует служебную страницу (legal/service)"""
        return f"""
    <main>
        <section class="section">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">01</span>
                        <span>Информация</span>
                    </div>
                    <h2>{page_name}</h2>
                </div>
                <div class="philosophy-content">
                    <p class="philosophy-text">
                        Страница "{page_name}" находится в разработке.
                    </p>
                </div>
            </div>
        </section>
    </main>
"""
    
    def generate_generic_page(self, page_name: str) -> str:
        """Генерирует универсальную страницу"""
        return f"""
    <main>
        <section class="section">
            <div class="container">
                <div class="section-header">
                    <h2>{page_name}</h2>
                    <p>Контент страницы находится в разработке.</p>
                </div>
            </div>
        </section>
    </main>
"""
    
    def generate_html(self, page: dict) -> str:
        """Генерирует полный HTML-файл"""
        page_name = page.get("name", "Страница")
        page_url = page.get("url", "/")
        
        # Определяем title и description
        title = f"{page_name} | 103vet.by"
        description = f"Страница {page_name} сайта 103vet.by"
        
        # Генерируем контент
        content = self.generate_page_content(page)
        
        # Собираем полный HTML
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    <style>
{self.css_content}
    </style>
</head>
<body>
{self.generate_navigation()}
{content}
{self.generate_footer()}
{self.js_code}
</body>
</html>"""
        
        return html
    
    def save_page(self, page: dict, html_content: str):
        """Сохраняет HTML-файл"""
        page_url = page.get("url", "/")
        
        # Определяем путь к файлу
        if page_url == "/":
            file_path = self.output_dir / "index.html"
        else:
            # Убираем начальный и конечный слэши
            url_path = page_url.strip("/")
            file_path = self.output_dir / url_path / "index.html"
        
        # Создаём папку если нужно
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем файл
        file_path.write_text(html_content, encoding="utf-8")
        
        print(f"✅ {page.get('name', 'Unknown')}")
        print(f"   → {file_path.relative_to(self.output_dir)}")
    
    def run(self):
        """Запускает генерацию всех страниц"""
        pages = self.site_map.get("pages", [])
        
        print(f"\n🚀 Начинаю генерацию {len(pages)} страниц...\n")
        
        generated = 0
        errors = 0
        
        for page in pages:
            try:
                html_content = self.generate_html(page)
                self.save_page(page, html_content)
                generated += 1
            except Exception as e:
                print(f"❌ Ошибка генерации {page.get('name', 'Unknown')}: {str(e)}")
                errors += 1
        
        print("\n" + "="*70)
        print("ИТОГОВЫЙ ОТЧЁТ")
        print("="*70)
        print(f"✅ Успешно сгенерировано: {generated} страниц")
        print(f"❌ Ошибок: {errors}")
        print(f"📁 Путь: {self.output_dir}")
        print("="*70)
        
        return errors == 0


def main():
    parser = argparse.ArgumentParser(description="Writer AI Pro v2.2")
    parser.add_argument("--site-map", required=True, help="Путь к site_map.json")
    parser.add_argument("--css", required=True, help="Путь к styles.css")
    parser.add_argument("--output-dir", required=True, help="Директория вывода")
    args = parser.parse_args()
    
    writer = WriterV22(args.site_map, args.css, args.output_dir)
    success = writer.run()
    
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
