import json
import re
import yaml
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY_FILE = Path("data/topic_registry.json")
OUTPUT_DIR = Path("data/generated_content")
MAX_LINKS_PER_PAGE = 4
MIN_ANCHOR_LENGTH = 3
MAX_ANCHOR_LENGTH = 5

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("topics", [])
    return []

def transliterate(text: str) -> str:
    """Транслитерирует кириллицу в латиницу"""
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    result = []
    for char in text.lower():
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isascii() and (char.isalnum() or char in '-_'):
            result.append(char)
        else:
            result.append('-')
    return ''.join(result)

def generate_topic_url(topic_name: str, site_key: str, sites: dict) -> str:
    """Генерирует читаемый URL для темы"""
    site_url = sites.get(site_key, {}).get("url", "")
    if not site_url:
        return ""
    
    base_url = site_url.rstrip("/")
    
    # Транслитерируем и создаём slug
    slug = transliterate(topic_name)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')[:100]  # Ограничиваем длину
    
    return base_url + "/" + slug + ".html"

def get_stop_words():
    return {'что', 'при', 'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'а', 'но', 'же', 'ли', 'бы', 'то', 'как', 'так', 'не', 'ни', 'да', 'или', 'если', 'когда', 'где', 'кто', 'первый', 'первые', 'признак', 'признаки'}

def find_meaningful_anchors(text: str, topic_name: str) -> List[str]:
    """Находит осмысленные якоря для ссылки"""
    topic_lower = topic_name.lower()
    topic_words = topic_lower.split()
    stop_words = get_stop_words()
    
    # Убираем стоп-слова из темы
    meaningful_words = [w for w in topic_words if w not in stop_words and len(w) > 2]
    
    if not meaningful_words:
        return []
    
    anchors = []
    
    # Ищем полные фразы из темы (2-5 слов подряд)
    for i in range(len(meaningful_words)):
        for length in range(2, min(6, len(meaningful_words) - i + 1)):
            phrase = ' '.join(meaningful_words[i:i+length])
            if phrase in text.lower():
                anchors.append(phrase)
    
    # Если не нашли полных фраз, ищем отдельные значимые слова в контексте
    if not anchors:
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_words = set(re.findall(r'\w+', sentence_lower))
            
            # Находим значимые слова темы, которые есть в предложении
            matched = [w for w in meaningful_words if w in sentence_words]
            
            if len(matched) >= 2:
                # Берём 2-3 слова подряд из предложения
                for i in range(len(matched) - 1):
                    anchor = matched[i] + ' ' + matched[i+1]
                    if anchor in sentence_lower:
                        anchors.append(anchor)
                        break
    
    # Убираем дубликаты
    return list(set(anchors))

def is_anchor_quality(anchor: str) -> bool:
    """Проверяет качество якоря"""
    words = anchor.split()
    
    # Длина
    if len(words) < MIN_ANCHOR_LENGTH or len(words) > MAX_ANCHOR_LENGTH:
        return False
    
    # Не должен начинаться/заканчиваться на предлог
    prepositions = ['при', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о']
    if words[0] in prepositions or words[-1] in prepositions:
        return False
    
    # Не должен содержать только стоп-слова
    stop_words = get_stop_words()
    meaningful = [w for w in words if w not in stop_words]
    if len(meaningful) < 2:
        return False
    
    return True

def check_ethical_linking(source_topic: str, target_topic: str) -> bool:
    """Проверяет этическую уместность ссылки"""
    source_lower = source_topic.lower()
    target_lower = target_topic.lower()
    
    forbidden_pairs = [
        ("корм", "усыпление"),
        ("питание", "усыпление"),
        ("вакцин", "усыпление"),
        ("профилактик", "усыпление"),
        ("щенок", "усыпление"),
        ("котён", "усыпление"),
    ]
    
    for source_kw, target_kw in forbidden_pairs:
        if source_kw in source_lower and target_kw in target_lower:
            return False
    
    return True

def get_topic_priority(topic: dict) -> int:
    """Возвращает приоритет темы"""
    targets = topic.get("targets", {})
    emotional_tier = targets.get("emotional", {}).get("target_emotional_tier", "SILVER")
    emergency = targets.get("actionability", {}).get("emergency_priority", False)
    
    priority = 0
    if emotional_tier == "PLATINUM":
        priority += 30
    elif emotional_tier == "GOLD":
        priority += 20
    elif emotional_tier == "SILVER":
        priority += 10
    
    if emergency:
        priority += 20
    
    return priority

def run_linker_ai_v5():
    print("="*70)
    print("LINKER AI v5: СЕМАНТИЧЕСКИЙ ЛИНКЕР НОВОГО ПОКОЛЕНИЯ")
    print("="*70)
    print("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    # Находим последний HTML-файл
    html_files = list(OUTPUT_DIR.glob("*.html"))
    if not html_files:
        print("HTML-файлы не найдены")
        return
    
    filepath = max(html_files, key=lambda p: p.stat().st_mtime)
    current_topic_name = filepath.stem.replace("_", " ").replace("?", "").replace("!", "").replace(".", "").replace(",", "").strip()
    
    print("Файл: " + str(filepath))
    print("Текущая тема: " + current_topic_name)
    
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    topics = load_registry()
    sites = load_sites()
    
    print("Тем в реестре: " + str(len(topics)))
    
    # Собираем потенциальные ссылки
    potential_links = []
    
    for topic in topics:
        topic_name = topic.get("name", "")
        topic_site = topic.get("site", "main")
        
        # Пропускаем текущую тему (self-linking) — нормализуем обе строки
        topic_norm = re.sub(r'[^a-zа-яё0-9]', '', topic_name.lower())
        current_norm = re.sub(r'[^a-zа-яё0-9]', '', current_topic_name.lower())
        if topic_norm == current_norm:
            continue
        
        # Проверяем этическую уместность
        if not check_ethical_linking(current_topic_name, topic_name):
            continue
        
        # Генерируем URL
        target_url = generate_topic_url(topic_name, topic_site, sites)
        if not target_url:
            continue
        
        # Находим якоря
        anchors = find_meaningful_anchors(text, topic_name)
        
        for anchor in anchors:
            if not is_anchor_quality(anchor):
                continue
            
            priority = get_topic_priority(topic)
            
            potential_links.append({
                "anchor": anchor,
                "url": target_url,
                "topic": topic_name,
                "priority": priority
            })
    
    # Сортируем по приоритету
    potential_links.sort(key=lambda x: x["priority"], reverse=True)
    
    # Убираем дубликаты по якорям
    seen_anchors = set()
    unique_links = []
    for link in potential_links:
        if link["anchor"] not in seen_anchors:
            seen_anchors.add(link["anchor"])
            unique_links.append(link)
    
    # Ограничиваем количество
    links_to_insert = unique_links[:MAX_LINKS_PER_PAGE]
    
    print("\nНайдено потенциальных ссылок: " + str(len(potential_links)))
    print("Уникальных ссылок: " + str(len(unique_links)))
    print("Будет вставлено: " + str(len(links_to_insert)))
    
    # Вставляем ссылки
    if links_to_insert:
        html_str = html_content
        
        for link in links_to_insert:
            anchor = link["anchor"]
            url = link["url"]
            topic = link["topic"]
            
            link_html = '<a href="' + url + '" title="Подробнее: ' + topic + '">' + anchor + '</a>'
            
            pattern = re.compile(re.escape(anchor), re.IGNORECASE)
            new_html, count = pattern.subn(link_html, html_str, count=1)
            
            if count > 0:
                html_str = new_html
                print("  Вставлена: '" + anchor + "' -> " + url)
        
        # Сохраняем
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_str)
        
        print("\nФайл обновлён: " + str(filepath))
    else:
        print("\nПодходящих ссылок не найдено")
    
    print("\n" + "="*70)
    print("ИТОГОВЫЙ ОТЧЁТ LINKER AI v5")
    print("="*70)
    print("Ссылок вставлено: " + str(len(links_to_insert)))
    print("Максимум: " + str(MAX_LINKS_PER_PAGE))
    print("="*70)

if __name__ == "__main__":
    run_linker_ai_v5()
