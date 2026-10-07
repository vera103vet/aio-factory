import sys
import argparse
import json
import re
from pathlib import Path
from datetime import datetime

REGISTRY_FILE = Path("data/topic_registry.json")
EXPERT_KNOWLEDGE_DIR = Path("data/expert_knowledge")

def parse_args():
    parser = argparse.ArgumentParser(description='Writer AI Pro v2.1')
    parser.add_argument('--topic', type=str, required=True, help='Тема статьи')
    parser.add_argument('--output', type=str, required=True, help='Путь к выходному HTML-файлу')
    parser.add_argument('--page-type', type=str, default='article', help='Тип страницы: article, how-to, guide, blog, service, legal')
    return parser.parse_args()

def generate_legal_html(topic: str) -> str:
    """Генерирует юридическую/служебную страницу с правильными дисклеймерами"""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} | 103vet.by</title>
    <meta name="description" content="{topic} ветеринарной клиники 103vet.by.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../styles.css">
</head>
<body>
    <nav class="nav">
        <a href="../../" class="nav-logo">103vet.by</a>
        <ul class="nav-menu">
            <li><a href="../../">Главная</a></li>
            <li><a href="../../guide/">Руководства</a></li>
        </ul>
    </nav>

    <main>
        <section class="hero" style="min-height: 50vh;">
            <div class="hero-content">
                <div class="hero-meta">
                    <span class="section-number">01</span>
                    <span>Официальная информация</span>
                </div>
                <h1>{topic}</h1>
            </div>
        </section>

        <section class="section">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">02</span>
                        <span>Условия и положения</span>
                    </div>
                    <h2>Важная информация</h2>
                </div>
                <div style="max-width: 800px; margin: 0 auto; font-size: 1.05rem; line-height: 1.8; color: var(--text-secondary);">
                    <p>Данный раздел содержит официальную информацию, регулирующую использование ресурсов ветеринарной клиники 103vet.by.</p>
                    <br>
                    <p>Мы стремимся предоставлять достоверную и актуальную информацию о здоровье животных, паллиативном уходе и ветеринарных услугах. Однако материалы сайта носят исключительно информационный характер.</p>
                    <br>
                    <div style="background: var(--bg-secondary); padding: 2rem; border-radius: 16px; border-left: 4px solid var(--ochre);">
                        <strong>⚠️ Медицинский дисклеймер:</strong><br>
                        Информация, представленная на сайте 103vet.by, не заменяет профессиональную ветеринарную консультацию, диагностику или лечение. При любых признаках ухудшения состояния здоровья вашего питомца немедленно обратитесь к квалифицированному ветеринарному врачу.
                    </div>
                </div>
            </div>
        </section>

        <section class="palliative">
            <div class="palliative-content">
                <div class="palliative-badge">Остались вопросы?</div>
                <h2>Свяжитесь с нами</h2>
                <p>Наши специалисты готовы ответить на ваши вопросы в рабочее время.</p>
                <a href="tel:+37529XXXXXXX" class="btn btn-primary">📞 Позвонить в клинику</a>
            </div>
        </section>
    </main>

    <footer>
        <div class="footer-content">
            <div class="footer-brand">
                <h3>103vet.by</h3>
                <p>Профессиональная ветеринарная помощь с заботой о ваших питомцах.</p>
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
        </div>
    </footer>
</body>
</html>"""

def generate_service_html(topic: str) -> str:
    """Генерирует служебную страницу (О проекте, Контакты, FAQ)"""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} | 103vet.by</title>
    <meta name="description" content="{topic} ветеринарной клиники 103vet.by.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Playfair+Display:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../styles.css">
</head>
<body>
    <nav class="nav">
        <a href="../../" class="nav-logo">103vet.by</a>
        <ul class="nav-menu">
            <li><a href="../../">Главная</a></li>
            <li><a href="../../guide/">Руководства</a></li>
        </ul>
    </nav>

    <main>
        <section class="hero" style="min-height: 50vh;">
            <div class="hero-content">
                <div class="hero-meta">
                    <span class="section-number">01</span>
                    <span>Информация для владельцев</span>
                </div>
                <h1>{topic}</h1>
            </div>
        </section>

        <section class="section">
            <div class="container">
                <div class="section-header">
                    <div class="section-label">
                        <span class="section-number">02</span>
                        <span>Подробности</span>
                    </div>
                    <h2>Всё, что вам нужно знать</h2>
                </div>
                <div style="max-width: 800px; margin: 0 auto; font-size: 1.05rem; line-height: 1.8; color: var(--text-secondary);">
                    <p>Раздел находится в стадии наполнения актуальной информацией. Мы регулярно обновляем данные, чтобы предоставить вам максимально полезные и точные сведения о работе клиники 103vet.by.</p>
                    <br>
                    <p>Если вы не нашли ответ на свой вопрос, пожалуйста, свяжитесь с нами любым удобным способом. Мы всегда рады помочь вам и вашим питомцам.</p>
                    <br>
                    <div style="background: var(--bg-secondary); padding: 2rem; border-radius: 16px; border-left: 4px solid var(--sage);">
                        <strong>💡 Помните:</strong><br>
                        Информация на сайте не заменяет очную консультацию ветеринарного врача. При любых тревожных симптомах обращайтесь к специалистам.
                    </div>
                </div>
            </div>
        </section>

        <section class="palliative">
            <div class="palliative-content">
                <div class="palliative-badge">Мы на связи</div>
                <h2>Нужна помощь?</h2>
                <p>Наши координаторы ответят на ваши вопросы и помогут записаться на приём.</p>
                <a href="tel:+37529XXXXXXX" class="btn btn-primary">📞 Получить консультацию</a>
            </div>
        </section>
    </main>

    <footer>
        <div class="footer-content">
            <div class="footer-brand">
                <h3>103vet.by</h3>
                <p>Профессиональная ветеринарная помощь с заботой о ваших питомцах.</p>
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
        </div>
    </footer>
</body>
</html>"""

def main():
    args = parse_args()
    
    print("="*70)
    print("WRITER AI PRO v2.1: Генерация PLATINUM-контента")
    print("="*70)
    print(f"📝 Тема: {args.topic}")
    print(f"📁 Вывод: {args.output}")
    print(f"📄 Тип: {args.page_type}")
    print("="*70)
    
    # Выбираем шаблон в зависимости от типа страницы
    if args.page_type in ['legal', 'service']:
        print(f"✅ Используется специализированный шаблон: {args.page_type}")
        if args.page_type == 'legal':
            html_content = generate_legal_html(args.topic)
        else:
            html_content = generate_service_html(args.topic)
    else:
        print("⚠️ Для данного типа страницы используется стандартный шаблон (требуется доработка базы знаний)")
        html_content = f"<!DOCTYPE html><html><head><title>{args.topic}</title></head><body><h1>{args.topic}</h1><p>Контент в разработке.</p></body></html>"
    
    # Создаём папку если нужно
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем файл
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Контент сохранён: {output_path}")
    print(f"📊 Размер: {len(html_content)} символов")
    print("="*70)

if __name__ == "__main__":
    main()
