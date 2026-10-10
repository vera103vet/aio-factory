# 🤖 Реестр агентов AIO-Symphony

**Дата создания:** 10.10.2026
**Всего агентов:** 61
**Папка:** `agents/`
**Версия системы:** 1.2

---

##  Оглавление

1. [Архитектура системы](#архитектура-системы)
2. [Словарь терминов](#словарь-терминов)
3. [Агенты](#агенты)
   - [aio_geo_seo_architect.py](#aio_geo_seo_architectpy)
4. [Сценарии использования](#сценарии-использования)

---

## ️ Архитектура системы

### Поток данных

```
[Входные данные] → [SEO Architect] → [Content Map]
                        ↓
[AIO/GEO Architect] → [HTML Template + Schema.org]
                        ↓
[Writer] → [Chief Editor] → [Critic] → [Auditor Network]
                                                ↓
                                    [12 Local Auditors] → [Validator] → [Deploy]
```

### Уровни масштабирования
- **Уровень 1**: ~60 страниц (полная генерация в памяти)
- **Уровень 2**: 150-500 страниц (батчинг по 20 страниц)
- **Уровень 3**: 1000-5000+ страниц (распределённая генерация, SQLite)

---

## 📖 Словарь терминов

| Термин | Описание | Пример |
|--------|----------|--------|
| **BLUF** | Bottom Line Up Front — прямой ответ в начале раздела | "Паллиативный уход — это..." |
| **YMYL** | Your Money Your Life — контент о здоровье/финансах | Ветеринарные статьи |
| **E-E-A-T** | Experience, Expertise, Authoritativeness, Trustworthiness | Ссылки на WSAVA, IRIS |
| **Schema.org** | Стандарт микроразметки | JSON-LD для MedicalWebPage |
| **Каннибализация** | Конкуренция страниц за один ключ | Две страницы про "уход за собакой" |
| **Content Map** | Карта контента с темами и ключами | `content_map_enriched.json` |
| **Project Config** | Конфигурация бренда | `project_config.json` |
| **AIO** | Answer Engine Optimization | Оптимизация для AI-поисковиков |
| **GEO** | Generative Engine Optimization | Оптимизация для генеративных движков |
| **Core Web Vitals** | Метрики производительности Google | LCP, FID, CLS |
| **NAP** | Name, Address, Phone | Для локального SEO |

---

## 📋 Агенты

###  Технический архитектор (AIO/GEO)

---

### 📄 `aio_geo_seo_architect.py`

#### 🏷️ Мета-информация
| Поле | Значение |
|------|----------|
| **Роль в системе** | Технический архитектор AIO/GEO |
| **Версия** | 1.1 |
| **Дата** | 10 октября 2026 г. |
| **Приоритет** | 10 (Критически важный) |
| **Размер** | ~7.0 КБ |
| **Класс** | `AIOGeoSEOArchitect` |
| **Зависимости** | `json`, `pathlib.Path` |

#### 🎯 Роль в системе
Агент отвечает за **машинную читаемость, семантическую структуру и производительность** веб-страниц. Интегрирует **10 скилов QWEN AIO/GEO SKILLS LIBRARY** для оптимизации под алгоритмы 2026 года (Google AI Overviews, Perplexity, ChatGPT, Yandex).

**Ключевая особенность:** это **промпт-инженер**, а не генератор контента. Его главная ценность — `SYSTEM_PROMPT` (строка с 10 скилами), который передаётся LLM. Сам агент не генерирует HTML — он подготавливает инструкции для Writer и Chief Editor.

#### 🔄 Взаимодействие с другими агентами
```
seo_architect.py (стратег контента)
    ↓ передаёт темы и ключевые слова
aio_geo_seo_architect.py (технический архитектор)
    ↓ передаёт SYSTEM_PROMPT с подставленным брендом
writer.py / chief_editor.py
    ↓ генерируют контент по промпту
local_auditor_*.py (сеть аудиторов)
    ↓ проверяют результат
seo_quality_auditor.py (второй страж)
    ↓ финальная проверка на каннибализацию
```

#### 📥 Входные данные
1. **`project_slug: str`** (опционально) — slug проекта, например `"dostoinyi-uhod"`
2. **Файл `projects/{slug}/project_config.json`** — конфигурация бренда

#### 📤 Выходные данные
1. **`resolve_prompt() → str`** — системный промпт с подставленными значениями бренда (готов к передаче LLM).
2. **`project_config: dict`** — загруженная конфигурация проекта.

#### 🏗️ Структура класса `AIOGeoSEOArchitect`
- **`__init__(self, project_slug: str = None)`**: Инициализирует атрибуты. Если передан `project_slug`, вызывает `load_project_config()`.
- **`load_project_config(self, project_slug: str)`**: Загружает `projects/{slug}/project_config.json`. Если файл не найден, использует значения по умолчанию (103vet.by).
- **`resolve_prompt(self) -> str`**: Подставляет 5 плейсхолдеров (`{{BRAND_NAME}}`, `{{BRAND_URL}}`, `{{LOGO_URL}}`, `{{CITY}}`, `{{AUTHOR_NAME}}`) в `SYSTEM_PROMPT` и возвращает готовую строку.

#### 🧠 SYSTEM_PROMPT — 10 скилов GEO (из Knowledge Base)
1. **СКИЛ 1: HTML-АРХИТЕКТУРА** — `<!DOCTYPE html>`, `<html lang="ru-RU">`, строгий порядок `<head>`, семантические теги (`<main>`, `<article>`), один `<h1>`, иерархия h1→h2→h3, доступность (a11y).
2. **СКИЛ 2: BLUF + CHUNKING** — прямой ответ в первых 1-2 предложениях каждого `<h2>`, абзацы по 2-3 предложения, ключевые факты в `<strong>`, списки `<ul>`/`<ol>`, YMYL-семантика (WSAVA, IRIS).
3. **СКИЛ 3: SCHEMA.ORG (JSON-LD)** — комбинированная схема `MedicalWebPage` + `MedicalCondition` + `Person` + `Organization` с динамическими плейсхолдерами.
4. **СКИЛ 4: CORE WEB VITALS** — LCP (WebP, lazy-loading), FID (async/defer), CLS (width/height для изображений).
5. **СКИЛ 5: AIO/GEO ОПТИМИЗАЦИЯ** — структура для Google AI Overviews, ссылки на PubMed для Perplexity, естественный язык для ChatGPT, FAQ/HowTo для Yandex.
6. **СКИЛ 6: E-E-A-T** — указание авторов с должностями, ссылки на протоколы, осторожный язык ("может помочь"), реальные кейсы.
7. **СКИЛ 7: ФИЛОСОФИЯ БРЕНДА** — тональность "Пространство спокойствия для людей и безопасности для животных". **Запреты**: цены, конкретные имена врачей, агрессивный маркетинг.
8. **СКИЛ 8: ПЕРЕЛИНКОВКА** — естественные анкоры, минимум 3-5 внутренних ссылок на страницу, хлебные крошки.
9. **СКИЛ 9: LOCAL SEO** — единообразие NAP, геотаргетинг (город в title, description, h1).
10. **СКИЛ 10: ЧЕК-ЛИСТ АУДИТА** — 10 пунктов проверки перед публикацией (валидный HTML, мета-теги, иерархия, семантика, JSON-LD, BLUF, YMYL, бренд, перелинковка, изображения).

#### 🎬 Примеры использования
**Пример 1: Базовое использование**
```python
from agents.aio_geo_seo_architect import AIOGeoSEOArchitect
architect = AIOGeoSEOArchitect()
prompt = architect.resolve_prompt() # Вернёт промпт с дефолтным брендом 103vet.by
```

**Пример 2: С конкретным проектом**
```python
architect = AIOGeoSEOArchitect(project_slug="dostoinyi-uhod")
prompt = architect.resolve_prompt()
# Теперь prompt содержит: {{BRAND_NAME}} → "Достойный уход", {{CITY}} → "Минск" и т.д.
```

#### ⚠️ Типичные ошибки и Troubleshooting
| Ошибка | Причина | Решение |
|--------|---------|---------
| `project_config = None` | `project_slug` не передан при инициализации | Вызвать `AIOGeoSEOArchitect(project_slug="...")` |
| Плейсхолдеры `{{BRAND_NAME}}` не заменены | Файл `project_config.json` не найден | Создать файл по пути `projects/{slug}/project_config.json` |
| `json.JSONDecodeError` | Ошибка синтаксиса в `project_config.json` | Проверить файл через `python3 -m json.tool projects/.../project_config.json` |

#### 📝 Текущие ограничения
1. **Методы-заглушки**: в коде нет методов `generate_content_map()`, `validate_html_architecture()`, `generate_schema_markup()`. Агент только готовит промпт.
2. **Нет валидации JSON**: при невалидном `project_config.json` будет выброшено исключение.
3. **Нет кэширования**: каждый вызов `resolve_prompt()` делает полную замену строк.
4. **Только русский язык**: промпт жёстко задан на русском (`lang="ru-RU"`).

---

*Продолжение следует... Изучены 1 из 61 агентов*
