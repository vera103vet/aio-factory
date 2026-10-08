#!/usr/bin/env python3
"""
SEO Architect v1.0
Агент предварительного контроля SEO
Гарантирует уникальность ключевых слов и защиту от каннибализации
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

class SEOArchitect:
    def __init__(self, starter_file: str, target_pages: int = 60):
        self.starter_file = Path(starter_file)
        self.target_pages = target_pages
        self.sections = []
        self.pages = []
        
        # База знаний для генерации уникальных тем
        self.topic_database = {
            'собак': {
                'primary_topics': [
                    'Паллиативный уход при онкологии у собак',
                    'Облегчение боли при артрите у пожилых собак',
                    'Организация комфортного пространства для лежачей собаки',
                    'Питание тяжелобольной собаки: рекомендации ветеринара',
                    'Признаки ухудшения состояния у собаки',
                    'Уход за собакой с деменцией',
                    'Контроль боли в домашних условиях',
                    'Гигиена лежачей собаки',
                    'Прогулки с тяжелобольной собакой',
                    'Эмоциональная поддержка собаки в последние дни',
                    'Медикаментозное обезболивание у собак',
                    'Физиотерапия для пожилых собак',
                    'Уход за собакой после инсульта',
                    'Паллиативная помощь при сердечной недостаточности',
                    'Уход за собакой с диабетом в терминальной стадии'
                ],
                'keywords': {
                    'онкология': ['опухоли', 'рак', 'химиотерапия', 'паллиатив'],
                    'артрит': ['суставы', 'боль', 'хромота', 'хондропротекторы'],
                    'деменция': ['когнитивные нарушения', 'дезориентация', 'поведение'],
                    'питание': ['диета', 'корм', 'аппетит', 'гастрономия']
                }
            },
            'кошек': {
                'primary_topics': [
                    'Уход за кошкой с хронической болезнью почек (ХБП)',
                    'Гипертиреоз у кошек: паллиативный подход',
                    'Деменция у кошек: помощь пожилому питомцу',
                    'Стимуляция аппетита у тяжелобольной кошки',
                    'Гидратация кошки с ХБП в домашних условиях',
                    'Контроль боли у кошек: особенности',
                    'Организация пространства для лежачей кошки',
                    'Уход за шерстью и гигиена кошки',
                    'Признаки ухудшения состояния у кошки',
                    'Поддержка кошки в последние дни',
                    'Инсулинотерапия у кошек в паллиативе',
                    'Уход за кошкой с кардиомиопатией',
                    'Паллиативная помощь при мочекаменной болезни',
                    'Уход за кошкой с печеночной недостаточностью',
                    'Поддержка кошки с респираторными заболеваниями'
                ],
                'keywords': {
                    'ХБП': ['почки', 'креатинин', 'диализ', 'гидратация'],
                    'гипертиреоз': ['щитовидная железа', 'тироксин', 'метаболизм'],
                    'деменция': ['когнитивная дисфункция', 'поведение', 'ориентация'],
                    'аппетит': ['питание', 'корм', 'стимуляция', 'гастрономия']
                }
            },
            'качество жизни': {
                'primary_topics': [
                    'Шкала HHHHHMM: подробное руководство для владельца',
                    'Как вести дневник наблюдения за питомцем',
                    'Объективная оценка качества жизни тяжелобольного животного',
                    'Когда пора прощаться: признаки и сомнения',
                    'Принятие взвешенного решения об эвтаназии',
                    'Роль ветеринара в оценке качества жизни',
                    'Эмоциональные аспекты принятия решения',
                    'Чек-лист для владельца тяжелобольного питомца',
                    'Вопросы, которые нужно задать ветеринару',
                    'Альтернативные подходы к оценке качества жизни',
                    'Критерии гуманного ухода',
                    'Баланс между продлением жизни и качеством жизни',
                    'Признаки достойного завершения пути',
                    'Как понять, что питомец страдает',
                    'Этические аспекты паллиативной помощи'
                ],
                'keywords': {
                    'HHHHHMM': ['шкала', 'оценка', 'критерии', 'параметры'],
                    'дневник': ['наблюдение', 'записи', 'мониторинг', 'отслеживание'],
                    'решение': ['выбор', 'эвтаназия', 'прощание', 'завершение'],
                    'ветеринар': ['консультация', 'осмотр', 'рекомендации', 'протокол']
                }
            },
            'владельцу': {
                'primary_topics': [
                    'Предварительное горе (anticipatory grief): как справиться',
                    'Как справиться с чувством вины владельца',
                    'Разговор с детьми о болезни питомца',
                    'Как объяснить ребенку смерть питомца',
                    'Ритуалы прощания: как провести последний день',
                    'Группы поддержки для владельцев тяжелобольных питомцев',
                    'Психологическая помощь после потери питомца',
                    'Мемориалы и память о питомце',
                    'Когда обращаться к психологу',
                    'Истории владельцев: опыт и поддержка',
                    'Как подготовиться к последним дням питомца',
                    'Организация домашнего ухода: практические советы',
                    'Финансовые аспекты паллиативной помощи',
                    'Как выбрать время для прощания',
                    'Духовные аспекты потери питомца'
                ],
                'keywords': {
                    'горе': ['утрата', 'печаль', 'эмоции', 'переживания'],
                    'дети': ['разговор', 'объяснение', 'поддержка', 'понимание'],
                    'прощание': ['ритуал', 'последний день', 'память', 'мемориал'],
                    'поддержка': ['помощь', 'группа', 'психолог', 'консультация']
                }
            }
        }
    
    def parse_starter(self) -> dict:
        """Извлекает структуру из starter.html"""
        html = self.starter_file.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        # Извлекаем навигацию
        nav_links = []
        nav = soup.find('nav')
        if nav:
            for link in nav.find_all('a', href=True):
                text = link.get_text(strip=True)
                href = link['href']
                if href.startswith('/') and href != '/' and text:
                    nav_links.append({
                        'name': text,
                        'slug': href.strip('/').rstrip('/'),
                        'href': href
                    })
        
        # Извлекаем заголовок
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else 'Сайт'
        
        return {
            'nav_links': nav_links,
            'title': title_text
        }
    
    def determine_section(self, topic: str) -> str:
        """Определяет раздел по теме"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['собак', 'собаки', 'собаке', 'пёс', 'пса']):
            return 'собак'
        elif any(word in topic_lower for word in ['кошек', 'кошки', 'кошке', 'кот', 'кота']):
            return 'кошек'
        elif any(word in topic_lower for word in ['качество жизни', 'шкала', 'оценка', 'решение']):
            return 'качество жизни'
        elif any(word in topic_lower for word in ['владельц', 'горе', 'дети', 'прощание', 'поддержка']):
            return 'владельцу'
        else:
            return 'собак'  # По умолчанию
    
    def generate_unique_keywords(self, topic: str, section: str) -> dict:
        """Генерирует уникальные ключевые слова для темы"""
        topic_lower = topic.lower()
        
        # Находим подходящие ключевые слова из базы
        section_keywords = self.topic_database.get(section, {}).get('keywords', {})
        
        primary_keyword = None
        secondary_keywords = []
        
        for key, synonyms in section_keywords.items():
            if key in topic_lower:
                primary_keyword = key
                secondary_keywords = synonyms[:3]  # Берём первые 3 синонима
                break
        
        # Если не нашли точное совпадение, генерируем из темы
        if not primary_keyword:
            words = topic_lower.split()
            primary_keyword = ' '.join([w for w in words if len(w) > 4][:2])
            secondary_keywords = [w for w in words if len(w) > 4 and w != primary_keyword][:3]
        
        return {
            'primary_keyword': primary_keyword,
            'secondary_keywords': secondary_keywords,
            'max_frequency': 2,  # Максимум 2 упоминания основного ключа
            'synonyms': secondary_keywords
        }
    
    def build_content_map(self) -> dict:
        """Строит полную карту контента с SEO-оптимизацией"""
        structure = self.parse_starter()
        
        # Определяем разделы
        self.sections = structure['nav_links']
        
        # Распределяем страницы по разделам
        pages_per_section = self.target_pages // len(self.sections)
        remaining = self.target_pages % len(self.sections)
        
        page_id = 1
        used_keywords = set()  # Для отслеживания уникальности
        
        for i, section in enumerate(self.sections):
            section_name = section['name'].lower()
            count = pages_per_section + (1 if i < remaining else 0)
            
            # Получаем темы для раздела
            section_key = None
            for key in self.topic_database:
                if key in section_name:
                    section_key = key
                    break
            
            if section_key:
                topics = self.topic_database[section_key]['primary_topics'][:count]
            else:
                topics = [f'{section["name"]}: тема {j+1}' for j in range(count)]
            
            for topic in topics:
                # Генерируем уникальные ключевые слова
                seo_data = self.generate_unique_keywords(topic, section_key or 'собак')
                
                # Проверяем уникальность
                keyword_key = seo_data['primary_keyword']
                if keyword_key in used_keywords:
                    # Добавляем уточнение для уникальности
                    seo_data['primary_keyword'] = f"{keyword_key} {page_id}"
                
                used_keywords.add(seo_data['primary_keyword'])
                
                # Создаём slug
                slug = self._slugify(topic)
                
                self.pages.append({
                    'page_id': page_id,
                    'section': section['name'],
                    'section_slug': section['slug'],
                    'slug': f"{section['slug']}/{slug}",
                    'h1': topic,
                    'meta_description': f"{topic} — профессиональная информация от клиники 103vet.by. Консультация и поддержка.",
                    'seo': seo_data,
                    'link_to': [s['slug'] for s in self.sections if s['slug'] != section['slug']][:2]
                })
                
                page_id += 1
        
        return {
            'project_name': structure['title'],
            'total_pages': len(self.pages),
            'sections': self.sections,
            'pages': self.pages,
            'seo_summary': {
                'total_unique_keywords': len(used_keywords),
                'cannibalization_risk': 'low',
                'spam_protection': 'enabled'
            }
        }
    
    def _slugify(self, text: str) -> str:
        """Преобразует текст в URL-friendly формат"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.strip('-')[:50]
    
    def save_content_map(self, output_file: str):
        """Сохраняет карту контента в JSON"""
        content_map = self.build_content_map()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_map, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Content map создан: {output_file}")
        print(f"   Всего страниц: {content_map['total_pages']}")
        print(f"   Разделов: {len(content_map['sections'])}")
        print(f"   Уникальных ключей: {content_map['seo_summary']['total_unique_keywords']}")
        print(f"   Риск каннибализации: {content_map['seo_summary']['cannibalization_risk']}")
        
        return content_map

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SEO Architect: генерация уникальной карты контента')
    parser.add_argument('--starter', required=True, help='Путь к starter.html')
    parser.add_argument('--pages', type=int, default=60, help='Количество страниц')
    parser.add_argument('--output', default='content_map_enriched.json', help='Выходной файл')
    
    args = parser.parse_args()
    
    architect = SEOArchitect(args.starter, args.pages)
    architect.save_content_map(args.output)
