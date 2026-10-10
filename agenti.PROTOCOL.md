# 🤖 AIO-SYMPHONY: Реестр агентов

**Версия:** 1.0
**Дата создания:** 10 октября 2026 г.
**Статус:** Активный
**Назначение:** Полная документация всех агентов системы AIO-Symphony.

---

## 🎯 Назначение файла

Этот документ — живая карта системы агентов. Он служит:
- Справочником для разработчика
- Инструкцией по восстановлению
- Чек-листом при масштабировании
- Страховкой системы

---

## 🏗️ Архитектура системы агентов

Система построена по принципу двух стражей + сети специалистов:

1. Первый страж (до генерации) — SEO Architect планирует темы и ключи
2. Генерация — Writer, Chief Editor, Domain Expert Critic
3. Второй страж (после генерации) — SEO Quality Auditor
4. Сеть специализированных аудиторов — 12 агентов local_auditor_*.py
5. Технический архитектор — AIO/GEO SEO Architect (10 скилов GEO)

---

##  Реестр агентов

### Категория 1: Архитекторы и стратеги

- **SEO Architect** (agents/seo_architect.py) — Первый страж, стратег контента. Версия: 1.0
- **AIO/GEO SEO Architect** (agents/aio_geo_seo_architect.py) — Технический архитектор, 10 скилов GEO. Версия: 1.1, Приоритет: 10

### Категория 2: Генерация контента

- **Writer** (agents/writer.py) — Основной копирайтер. Версия: 2.2
- **Chief Editor** (agents/chief_editor.py) — Стилист и редактор. Версия: 1.1
- **Domain Expert Critic** (agents/domain_expert_critic.py) — Критик-эксперт. Версия: 2.1

### Категория 3: Контроль качества (Второй страж)

- **SEO Quality Auditor** (agents/seo_quality_auditor.py) — Контролёр переспама и каннибализации. Версия: 1.0
### Категория 4: Сеть специализированных аудиторов (12 агентов)

- local_auditor_html_structure.py — HTML-структура, семантика
- local_auditor_schema.py — Schema.org (JSON-LD)
- local_auditor_seo_basics.py — Базовое SEO
- local_auditor_content_quality.py — Качество контента, BLUF, YMYL
- local_auditor_brand.py — Философия бренда
- local_auditor_links.py — Перелинковка
- local_auditor_images.py — Изображения
- local_auditor_performance.py — Производительность
- local_auditor_mobile.py — Мобильная версия
- local_auditor_accessibility.py — Доступность (a11y)
- local_auditor_contacts.py — Контакты, NAP
- local_auditor_security.py — Безопасность

### Категория 5: Координация и сборка

- **Auditor Network** (agents/auditor_network.py) — Координатор сети. Версия: 2
- **Auditor AI** (agents/auditor_ai.py) — AI-аудитор. Версия: 15
- **Linker** (agents/linker.py) — Перелинковка. Версия: 5
- **Maestro** (agents/maestro.py) — Дирижёр пайплайна. Версия: 2
- **Registrar** (agents/registrar.py) — Регистрация. Версия: 2
- **Strategist** (agents/strategist.py) — Стратег. Версия: 2
- **Validator** (agents/validator.py) — Валидатор. Версия: 2.1
- **Deploy Agent** (agents/deploy_agent.py) — Деплой
- **Demand Collector** (agents/demand_collector.py) — Сборщик спроса
- **Serp Device Analyst** (agents/serp_device_analyst.py) — Аналитик SERP
- **Site Architect** (agents/site_architect.py) — Архитектор сайта
- **URL SEO Specialist** (agents/url_seo_specialist.py) — Специалист по URL
- **QA Validator** (agents/qa_validator.py) — QA-валидатор
- **Priority** (agents/priority.py) — Менеджер приоритетов
- **Orchestrator** (agents/orchestrator_v3.py) — Оркестратор. Версия: 3
---

## 📐 Правила масштабирования

### Уровень 1: Малые сайты (~60 страниц)
- Все агенты в стандартном режиме
- Полная генерация в памяти

### Уровень 2: Средние сайты (150-500 страниц)
- Обязательный батчинг (по 20 страниц)
- Чекпоинтинг каждые 10 страниц
- Очистка памяти между партиями

### Уровень 3: Основной сайт (1000-5000+ страниц)
- Распределённая генерация
- Хранение content_map в SQLite/JSONL
- Асинхронный аудит через Auditor Network

**ЗАПРЕЩЕНО:** Запускать пайплайн для Уровня 2 или 3 с настройками Уровня 1.

---

## 🔗 Схема взаимодействия агентов

Входные данные → Site Structure Analyzer → SEO Architect (1-й страж) → AIO/GEO SEO Architect → content_map_enriched.json → Writer → Chief Editor → Domain Expert Critic → Linker → SEO Quality Auditor (2-й страж) → Auditor Network → 12 local_auditor_*.py → QA Validator → Deploy Agent → Готовый сайт

---

## 🚨 Процедура восстановления агента

1. Откройте этот файл — здесь зафиксированы все агенты и версии
2. Проверьте историю Git: git log --oneline agents/{имя}.py
3. Найдите последний рабочий коммит
4. Выполните откат: git checkout {хеш} -- agents/{имя}.py
5. Проверьте синтаксис: python3 -c "from agents.{имя} import {Класс}; print(OK)"
6. Возобновите работу

---

## 📝 История изменений

- **Версия 1.0** | 10 октября 2026 г. | Первоначальная версия: все агенты AIO-Symphony зафиксированы.

---

**Этот документ — вторая страховка системы (наряду с PROTOCOL.md).**