from agents.registrar_v2 import add_topic

print("Добавляем релевантные темы для теста линкера...")

relevant_topics = [
    ("Судороги и приступы у собак: первая помощь", "nevrolog"),
    ("Неврологические заболевания у домашних животных", "nevrolog"),
    ("Как вести себя при приступе у питомца", "nevrolog"),
    ("Диагностика эпилепсии у собак и кошек", "nevrolog"),
]

for topic, site in relevant_topics:
    result = add_topic(topic, site)
    if "error" in result:
        print("  Пропущено: " + result["error"])
    else:
        print("  Добавлено: " + topic)

print("\nГотово! Теперь в реестре есть темы, релевантные эпилепсии.")
