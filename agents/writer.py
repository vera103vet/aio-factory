import json
from pathlib import Path

REGISTRY = Path("data/topic_registry.json")

def generate_full_geo_article(topic, keyword, target_site):
    brand = "103vet.by"
    philosophy = "Пространство спокойствия для людей и безопасности для животных"
    year = "2026"
    
    site_urls = {
        "main": "https://103vet.by/",
        "nevrolog": "https://nevrolog.103vet.by/",
        "usyplenie": "https://usyplenie.103vet.by/index.html",
        "vetminsk": "https://www.vetminsk.103vet.by/"
    }
    site_url = site_urls.get(target_site, "https://103vet.by/")
    
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} | {brand}</title>
    <meta name="description" content="{topic}. Экспертная информация от {brand}. {philosophy}.">
    <link rel="canonical" href="{site_url}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{topic}">
    <meta property="og:description" content="{philosophy}">
    <meta property="og:url" content="{site_url}">
    <meta property="og:type" content="article">
    <meta property="og:image" content="{site_url}logo.webp">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{topic}">
    <meta name="twitter:description" content="{philosophy}">
    <meta name="twitter:image" content="{site_url}logo.webp">
    
    <!-- Schema.org JSON-LD -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "MedicalWebPage",
      "mainEntity": {{
        "@type": "MedicalCondition",
        "name": "{topic}",
        "alternateName": "{keyword}"
      }},
      "headline": "{topic}",
      "datePublished": "{year}-10-01",
      "dateModified": "{year}-10-04",
      "author": {{
        "@type": "Organization",
        "name": "{brand}",
        "description": "{philosophy}",
        "url": "https://103vet.by"
      }},
      "publisher": {{
        "@type": "VeterinaryCare",
        "name": "{brand}",
        "logo": {{ "@type": "ImageObject", "url": "{site_url}logo.webp", "width": 1200, "height": 630 }}
      }}
    }}
    </script>
</head>
<body>
    <header>
        <nav>
            <a href="{site_url}">{brand}</a>
        </nav>
    </header>
    
    <main>
        <article>
            <h1>{topic}</h1>
            <p><strong>{philosophy}</strong></p>
            
            <section>
                <h2>Что нужно знать о {keyword.lower()}?</h2>
                <p><strong>Краткий ответ:</strong> Здесь будет прямой ответ на вопрос пользователя (принцип BLUF). Информация основана на международных протоколах WSAVA и IRIS.</p>
                <ul>
                    <li>Ключевой факт 1, связанный с запросом</li>
                    <li>Ключевой факт 2, подтверждающий экспертность</li>
                    <li>Ключевой факт 3, практическая рекомендация</li>
                </ul>
            </section>
            
            <section>
                <h2>Какие симптомы требуют внимания?</h2>
                <p><strong>Тревожные сигналы:</strong> Перечисление симптомов для раннего выявления проблемы.</p>
                <ul>
                    <li>Симптом 1</li>
                    <li>Симптом 2</li>
                    <li>Симптом 3</li>
                </ul>
            </section>
            
            <section>
                <h2>Какой протокол действий для владельца?</h2>
                <p><strong>Пошаговый алгоритм:</strong> Четкие действия без упоминания конкретных специалистов и цен.</p>
                <ol>
                    <li><strong>Шаг 1:</strong> Оценка состояния в спокойной обстановке</li>
                    <li><strong>Шаг 2:</strong> Обращение за профессиональной помощью</li>
                    <li><strong>Шаг 3:</strong> Соблюдение назначенных рекомендаций</li>
                </ol>
            </section>
            
            <section>
                <h2>Часто задаваемые вопросы (FAQ)</h2>
                
                <h3>Что делать при первых признаках?</h3>
                <p>Не заниматься самолечением. Безопасность животного превыше всего. Зафиксируйте симптомы и свяжитесь с {brand}.</p>
                
                <h3>Можно ли решить проблему онлайн?</h3>
                <p>Первичная оценка возможна, но точный диагноз требует очного осмотра или выезда специалиста.</p>
                
                <h3>Как получить помощь?</h3>
                <p>Свяжитесь со службой {brand} для получения экспертной оценки и организации визита.</p>
            </section>
        </article>
    </main>
    
    <footer>
        <p>&copy; {year} {brand}. {philosophy}.</p>
    </footer>
</body>
</html>"""
    
    return html

if __name__ == "__main__":
    topic = input("Введите тему статьи: ")
    keyword = input("Введите ключевую фразу: ")
    target_site = input("Целевой сайт (main/nevrolog/usyplenie/vetminsk): ")
    
    print("\n" + "="*70)
    print("СГЕНЕРИРОВАННЫЙ GEO-ОПТИМИЗИРОВАННЫЙ HTML (AIO 2026 + E-E-A-T)")
    print("="*70 + "\n")
    print(generate_full_geo_article(topic, keyword, target_site))
