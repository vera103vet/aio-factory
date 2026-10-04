import re
from pathlib import Path

RULES_FILE = Path("config/seo_rules.yaml")

def check_keyword_density(text, keyword):
    # Очистка текста от HTML-тегов для честного подсчета слов
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    
    # Подсчет общего количества слов
    words = re.findall(r'\b\w+\b', clean_text.lower())
    total_words = len(words)
    
    if total_words == 0:
        return {"error": "Текст пуст"}
    
    # Подсчет вхождений ключевого слова (с учетом словоформ)
    # Используем простое вхождение подстроки для базовой оценки
    keyword_lower = keyword.lower()
    keyword_count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', clean_text.lower()))
    
    # Расчет плотности в процентах
    density = (keyword_count / total_words) * 100
    
    # Правило из config: макс 2.0%
    max_density = 2.0
    
    result = {
        "total_words": total_words,
        "keyword_count": keyword_count,
        "density_percent": round(density, 2),
        "max_allowed": max_density,
        "is_safe": density <= max_density,
        "status": "✅ БЕЗОПАСНО (нет переспама)" if density <= max_density else f"⚠️ ПЕРЕСПАМ! Плотность {round(density, 2)}% превышает лимит {max_density}%"
    }
    
    return result

if __name__ == "__main__":
    print("="*60)
    print("ПРОВЕРКА ТЕКСТА НА ПЕРЕСПАМ (AIO/GEO 2026)")
    print("="*60)
    
    # Для теста возьмем небольшой пример текста
    sample_text = """
    Хроническая болезнь почек у кошек требует особого внимания. 
    Диета при хронической болезни почек у кошек должна быть низкобелковой. 
    Если у вашей кошки хроническая болезнь почек, диета и уход играют решающую роль.
    Всегда консультируйтесь с ветеринаром.
    """
    
    sample_keyword = "хроническая болезнь почек у кошек диета"
    
    print(f"\nПроверяемый ключ: '{sample_keyword}'")
    print(f"Текст для проверки:\n{sample_text}\n")
    
    result = check_keyword_density(sample_text, sample_keyword)
    
    print("РЕЗУЛЬТАТ АНАЛИЗА:")
    print(f"Всего слов: {result['total_words']}")
    print(f"Вхождений ключа: {result['keyword_count']}")
    print(f"Плотность: {result['density_percent']}%")
    print(f"Статус: {result['status']}")
