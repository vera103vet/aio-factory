from pathlib import Path

# Загружаем сгенерированный контент
content_file = Path("data/generated_content/что_делать_при_первых_признаках_эпилепсии_у_собаки.html")
content = content_file.read_text(encoding="utf-8")

print("="*70)
print("🧪 ВАЛИДАЦИЯ СГЕНЕРИРОВАННОГО КОНТЕНТА")
print("="*70)

# Проверка ключевых элементов PLATINUM-стандарта
checks = {
    "BLUF-ответ в начале": "Краткий ответ" in content,
    "Кликабельный телефон (tel:)": 'href="tel:' in content,
    "Модуль эмпатии": "Мы понимаем ваше беспокойство" in content,
    "Дерево решений (Если... то)": "Если симптомы" in content,
    "Чек-лист действий": "Чек-лист" in content,
    "Ссылка на WSAVA": "WSAVA" in content,
    "YMYL-дисклеймер": "<aside" in content and "не заменяет" in content,
    "Schema.org разметка": "application/ld+json" in content,
    "width/height у изображений": 'width="800"' in content,
    "Нет имён врачей": "Иванов" not in content and "Петров" not in content,
    "Нет цен": "руб" not in content.lower() and "стоимость" not in content.lower()
}

passed = sum(1 for v in checks.values() if v)
total = len(checks)

print(f"\n Результат: {passed}/{total} проверок пройдено\n")

for check, result in checks.items():
    status = "✅" if result else ""
    print(f"  {status} {check}")

print(f"\n{'='*70}")
if passed == total:
    print("🏆 ИДЕАЛЬНЫЙ РЕЗУЛЬТАТ! Контент соответствует всем стандартам PLATINUM!")
elif passed >= total * 0.8:
    print("✅ ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Контент на уровне GOLD+")
else:
    print("⚠️ Требует доработки")
print("="*70)
