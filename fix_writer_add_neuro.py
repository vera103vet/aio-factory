from pathlib import Path
import sys

filepath = Path("agents/writer_ai_pro_v2.py")
content = filepath.read_text(encoding="utf-8")

# Проверяем, есть ли уже модуль
if "module_neurology_expertise" in content:
    print("Модуль неврологии УЖЕ есть в Writer AI Pro.")
else:
    print("Добавляем модуль неврологии...")
    
    neuro_module = '''
def module_neurology_expertise():
    """Модуль неврологической экспертизы (требование Domain Expert Critic)"""
    return """
    <h3>Важные экспертные нюансы</h3>
    <ul>
        <li><strong>Различие между эпилепсией и реактивными судорогами:</strong> Не все судороги являются эпилепсией. Реактивные судороги могут возникать при отравлении, гипогликемии или печёночной энцефалопатии. Точный диагноз ставит только невролог после обследования.</li>
        <li><strong>Важность дневника приступов:</strong> Ведите дневник, фиксируя дату, время, продолжительность и характер каждого эпизода. Это бесценная информация для подбора терапии.</li>
        <li><strong>Постиктальная фаза:</strong> После приступа собака может быть дезориентирована, временно слепа или испытывать сильный голод. Это нормально и проходит в течение нескольких часов. Обеспечьте питомцу покой и безопасность в этот период.</li>
    </ul>
    """
'''
    
    # Вставляем модуль перед generate_platinum_content
    insert_point = content.find("def generate_platinum_content(")
    if insert_point != -1:
        content = content[:insert_point] + neuro_module + "\n" + content[insert_point:]
        print("Модуль добавлен перед generate_platinum_content.")
    else:
        print("ОШИБКА: не найдена функция generate_platinum_content")
        sys.exit(1)

# Проверяем, вызывается ли модуль
if "module_neurology_expertise()" not in content:
    print("Добавляем вызов модуля...")
    content = content.replace(
        "content += module_faq()",
        "content += module_faq()\n    content += module_neurology_expertise()"
    )
    print("Вызов модуля добавлен.")
else:
    print("Вызов модуля уже есть.")

filepath.write_text(content, encoding="utf-8")
print("Writer AI Pro v2.0 обновлён.")
