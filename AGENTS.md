# 🤖 Реестр агентов AIO-Symphony

**Дата генерации:** 10.10.2026 14:04
**Всего агентов:** 61
**Папка:** `agents/`

---

## 📑 Оглавление

- 🏗️ Архитекторы и стратеги
- 📦 Другие агенты
-  Аудиторы (общие)
- ️ Писатели и редакторы
- 📊 SEO и аналитика
- 🎼 Оркестрация и управление
- 🔗 Связывание и навигация
- 🎯 Сеть специализированных аудиторов
- ✅ Валидация и контроль качества

---

## 🏗️ Архитекторы и стратеги

### 📄 `aio_geo_seo_architect.py`

- **Размер:** 7.0 КБ
- **Класс:** `AIOGeoSEOArchitect`
- **Описание:** AIO/GEO SEO Architect — Технический архитектор
Интегрирует 10 скилов QWEN AIO/GEO SKILLS LIBRARY

Версия: 1.1
Дата: 10 октября 2026 г.
Приоритет: 10 (Критически важный)

Работает в связке с:
- seo_architect.py (стратег контента)
- seo_quality_auditor.py (контроль качества)
- local_auditor_*.py (сеть
- **Методы:** `load_project_config()`, `resolve_prompt()`

### 📄 `priority.py`

- **Размер:** 13.9 КБ
- **Описание:** Загружает данные о поисковом спросе

### 📄 `seo_architect.py`

- **Размер:** 16.8 КБ
- **Класс:** `SEOArchitect`
- **Описание:** SEO Architect v1.0
Агент предварительного контроля SEO
Гарантирует уникальность ключевых слов и защиту от каннибализации
- **Методы:** `parse_starter()`, `determine_section()`, `generate_unique_keywords()`, `build_content_map()`, `save_content_map()`

### 📄 `site_architect.py`

- **Размер:** 13.8 КБ
- **Описание:** Генерирует полную карту сайта из шаблона

### 📄 `strategist.py`

- **Размер:** 0.9 КБ
- **Описание:** Стратег: анализирует через check_cannibalization

### 📄 `strategist_v2.py`

- **Размер:** 13.4 КБ
- **Описание:** Анализирует конкурентный разрыв по теме (из auditor_ai_v9)

## 📦 Другие агенты

### 📄 `auditor.py`

- **Размер:** 6.8 КБ
- **Описание:** Проверяет одну страницу сайта на соответствие стандартам 2026

### 📄 `auditor_network.py`

- **Размер:** 10.0 КБ
- **Описание:** Загружает HTML сайта

### 📄 `auditor_network_v2.py`

- **Размер:** 14.1 КБ
- **Описание:** Аудитор: проверяет load_sites, load_registry, fetch_html, parse_site, analyze_strength

##  Аудиторы (общие)

### 📄 `auditor_ai.py`

- **Размер:** 7.7 КБ
- **Описание:** <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "VeterinaryCare",
  "name": "103vet.by - {site_name}",
  "url": "{url}",
  "description": "Профессиональная ветеринарная помощь. Пространство спокойствия для людей и безопасности для животных."
}}
</script>

### 📄 `auditor_ai_v10.py`

- **Размер:** 18.8 КБ
- **Описание:** КРИТЕРИЙ 1: УНИКАЛЬНОСТЬ ИНФОРМАЦИИ

### 📄 `auditor_ai_v11.py`

- **Размер:** 15.6 КБ
- **Описание:** КРИТЕРИЙ 1: CONVERSATIONAL TONE SCORE (Разговорный тон)

### 📄 `auditor_ai_v12.py`

- **Размер:** 19.6 КБ
- **Описание:** БАЗА ВЕТЕРИНАРНЫХ ТЕРМИНОВ С ЛОКАЛИЗАЦИЕЙ КУЛЬТУРНЫЕ МАРКЕРЫ ДЛЯ РАЗНЫХ РЫНКОВ

### 📄 `auditor_ai_v13.py`

- **Размер:** 20.4 КБ
- **Описание:** КРИТЕРИЙ 1: EMPATHY SCORE (Уровень эмпатии)

### 📄 `auditor_ai_v14.py`

- **Размер:** 19.5 КБ
- **Описание:** КРИТЕРИЙ 1: STEP-BY-STEP CLARITY (Чёткость пошаговых инструкций)

### 📄 `auditor_ai_v15.py`

- **Размер:** 20.5 КБ
- **Описание:** КРИТЕРИЙ 1: BIAS DETECTION (Обнаружение предвзятости)

### 📄 `auditor_ai_v4.py`

- **Размер:** 13.6 КБ
- **Описание:** База сущностей для ветеринарных тем (СУПЕРСИЛА 2)

### 📄 `auditor_ai_v5.py`

- **Размер:** 12.0 КБ
- **Описание:** Аудитор: проверяет load_sites, load_registry, fetch_html, parse_site, extract_entities

### 📄 `auditor_ai_v6.py`

- **Размер:** 10.8 КБ
- **Описание:** Устаревшие термины/протоколы (сигналы устаревания) Маркеры актуальности Авторитетные источники с датами обновлений

### 📄 `auditor_ai_v7.py`

- **Размер:** 11.4 КБ
- **Описание:** СУПЕРСИЛА 1: АНАЛИЗ ALT-ТЕКСТОВ ИЗОБРАЖЕНИЙ

### 📄 `auditor_ai_v8.py`

- **Размер:** 13.7 КБ
- **Описание:** Аудитор: проверяет load_sites, load_registry, fetch_html, parse_site, get_relevant_questions

### 📄 `auditor_ai_v9.py`

- **Размер:** 10.0 КБ
- **Описание:** Аудитор: проверяет load_sites, fetch_html, analyze_ai_readiness, scan_competitors, compare_with_competitors

### 📄 `auditor_v2.py`

- **Размер:** 16.5 КБ
- **Описание:** Вычисляет плотность ключевых слов

### 📄 `auditor_v3.py`

- **Размер:** 10.1 КБ
- **Описание:** Проверяет наличие запрещённых элементов (цены, имена)

## ️ Писатели и редакторы

### 📄 `chief_editor.py`

- **Размер:** 9.8 КБ
- **Описание:** Редактор: редактирует через load_rules, parse_html, check_brand_voice

### 📄 `chief_editor_v1_1.py`

- **Размер:** 1.6 КБ
- **Описание:** Chief Editor v1.1 — адаптер для chief_editor.py
Проверка тональности и читабельности

### 📄 `domain_expert_critic.py`

- **Размер:** 11.2 КБ
- **Описание:** Извлекает H1 из HTML контента

### 📄 `domain_expert_critic_v2_1.py`

- **Размер:** 2.5 КБ
- **Описание:** Парсит аргументы командной строки

### 📄 `writer.py`

- **Размер:** 7.0 КБ
- **Описание:** <!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} | {brand}</title>
    <meta name="description" content="{topic}. Экспертная информация от {brand}. {philosophy}.">
    <link rel="canonical

### 📄 `writer_ai_pro.py`

- **Размер:** 10.0 КБ
- **Описание:** Модуль 1: Прямой ответ + Mobile UX (решает проблемы v11 и Device Analyst)

### 📄 `writer_ai_pro_v2.py`

- **Размер:** 14.2 КБ
- **Описание:** Модуль 1: Прямой ответ + Mobile UX

### 📄 `writer_ai_pro_v2_1.py`

- **Размер:** 11.3 КБ
- **Описание:** Генерирует юридическую/служебную страницу с правильными дисклеймерами

### 📄 `writer_v2_2.py`

- **Размер:** 27.3 КБ
- **Класс:** `WriterV22`
- **Описание:** WRITER AI PRO v2.2
Генератор HTML-страниц со встроенными стилями и JavaScript
- **Методы:** `load_site_map()`, `load_css()`, `generate_navigation()`, `generate_footer()`, `generate_page_content()`, `generate_home_page()`, `generate_article_page()`, `generate_legal_page()`
  - *...и ещё 4 методов*

## 📊 SEO и аналитика

### 📄 `demand_collector.py`

- **Размер:** 9.1 КБ
- **Описание:** Загружает реестр тем

### 📄 `seo_quality_auditor.py`

- **Размер:** 8.0 КБ
- **Класс:** `SEOQualityAuditor`
- **Описание:** SEO Quality Auditor v1.0
Второй страж: проверяет сгенерированный контент на переспам и каннибализацию
- **Методы:** `load_content_map()`, `extract_text()`, `check_keyword_density()`, `check_cannibalization()`, `audit()`

### 📄 `serp_device_analyst.py`

- **Размер:** 26.1 КБ
- **Описание:** Эмулируем мобильный User-Agent по умолчанию, так как Google использует Mobile-First Indexing СУПЕРСИЛА 1: MOBILE UX & EMERGENCY READINESS

### 📄 `url_seo_specialist.py`

- **Размер:** 12.1 КБ
- **Описание:** Определяет тип контента по маркерам в названии

## 🎼 Оркестрация и управление

### 📄 `deploy_agent.py`

- **Размер:** 4.5 КБ
- **Класс:** `DeployAgent`
- **Описание:** DEPLOY AGENT
Создаёт ZIP, загружает на GitHub, создаёт бэкапы
- **Методы:** `create_zip()`, `create_backup()`, `upload_to_github()`, `run()`

### 📄 `maestro.py`

- **Размер:** 14.7 КБ
- **Описание:** Загружает JSON-отчёт с проверкой существования

### 📄 `maestro_v2.py`

- **Размер:** 8.7 КБ
- **Описание:** Загружает карту сайта из JSON

### 📄 `orchestrator_v3.py`

- **Размер:** 5.1 КБ
- **Класс:** `Orchestrator`
- **Описание:** MASTER ORCHESTRATOR v3
Главный агент, который координирует работу всей команды
- **Методы:** `log()`, `run_agent()`, `generate_site()`

### 📄 `registrar.py`

- **Размер:** 1.0 КБ
- **Описание:** Регистратор: регистрирует через add_topic

### 📄 `registrar_v2.py`

- **Размер:** 18.1 КБ
- **Описание:** === МОДУЛЬ ТЕМАТИЧЕСКОГО СООТВЕТСТВИЯ ===

## 🔗 Связывание и навигация

### 📄 `linker.py`

- **Размер:** 7.8 КБ
- **Описание:** Находит умные анкоры: от точных до фрагментарных

### 📄 `linker_ai_v5.py`

- **Размер:** 10.7 КБ
- **Описание:** Транслитерирует кириллицу в латиницу

## 🎯 Сеть специализированных аудиторов

### 📄 `local_auditor_accessibility.py`

- **Размер:** 2.4 КБ
- **Описание:** Local Auditor: Accessibility
Проверяет доступность (a11y)

### 📄 `local_auditor_brand.py`

- **Размер:** 2.2 КБ
- **Описание:** Local Auditor: Brand
Проверяет элементы брендинга

### 📄 `local_auditor_contacts.py`

- **Размер:** 2.2 КБ
- **Описание:** Local Auditor: Contacts
Проверяет наличие контактной информации

### 📄 `local_auditor_content_quality.py`

- **Размер:** 2.4 КБ
- **Описание:** Local Auditor: Content Quality
Проверяет качество и объём контента

### 📄 `local_auditor_html_structure.py`

- **Размер:** 2.0 КБ
- **Описание:** Local Auditor: HTML Structure
Проверяет базовую структуру HTML5

### 📄 `local_auditor_images.py`

- **Размер:** 1.9 КБ
- **Описание:** Local Auditor: Images
Проверяет изображения и alt-атрибуты

### 📄 `local_auditor_links.py`

- **Размер:** 2.3 КБ
- **Описание:** Local Auditor: Links
Проверяет ссылки на странице

### 📄 `local_auditor_mobile.py`

- **Размер:** 1.9 КБ
- **Описание:** Local Auditor: Mobile
Проверяет мобильную адаптацию

### 📄 `local_auditor_performance.py`

- **Размер:** 2.3 КБ
- **Описание:** Local Auditor: Performance
Проверяет производительность страницы

### 📄 `local_auditor_schema.py`

- **Размер:** 1.9 КБ
- **Описание:** Local Auditor: Schema
Проверяет микроразметку Schema.org

### 📄 `local_auditor_security.py`

- **Размер:** 2.3 КБ
- **Описание:** Local Auditor: Security
Проверяет безопасность HTML

### 📄 `local_auditor_seo_basics.py`

- **Размер:** 2.3 КБ
- **Описание:** Local Auditor: SEO Basics
Проверяет базовые SEO-элементы

## ✅ Валидация и контроль качества

### 📄 `qa_validator.py`

- **Размер:** 5.7 КБ
- **Класс:** `QAVValidator`
- **Описание:** QA VALIDATOR
Проверяет качество сгенерированных HTML-страниц
- **Методы:** `check_html_file()`, `run()`

### 📄 `validator.py`

- **Размер:** 2.8 КБ
- **Описание:** Хроническая болезнь почек у кошек требует особого внимания. 

### 📄 `validator_ai_v2.py`

- **Размер:** 13.8 КБ
- **Описание:** Парсит HTML и извлекает текст и структуру

### 📄 `validator_ai_v2_1.py`

- **Размер:** 1.4 КБ
- **Описание:** Парсит аргументы командной строки

---

*Документация сгенерирована автоматически скриптом `generate_agents_docs_v2.py`*