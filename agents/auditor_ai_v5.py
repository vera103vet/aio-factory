import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v5.json")

REFERENCE_GRAPHS = {
    "эпилепс": {
        "эпилепсия": ["судороги", "припадки", "ЭЭГ", "фенобарбитал", "невролог", "диагноз", "лечение"],
        "судороги": ["эпилепсия", "припадки", "мышцы", "потеря сознания"],
        "фенобарбитал": ["эпилепсия", "лечение", "побочные эффекты", "дозировка"],
        "ЭЭГ": ["эпилепсия", "диагностика", "мозг", "электрическая активность"]
    },
    "почек": {
        "ХБП": ["креатинин", "мочевин", "IRIS", "стадии", "диета", "фосфор", "почки"],
        "креатинин": ["ХБП", "почки", "анализ крови", "IRIS стадии"],
        "IRIS": ["ХБП", "стадии", "классификация", "протокол"],
        "диета": ["ХБП", "фосфор", "белок", "лечение"]
    },
    "онколог": {
        "опухоль": ["онкология", "биопсия", "метастазы", "химиотерапия", "диагноз"],
        "биопсия": ["опухоль", "диагностика", "гистология", "анализ"],
        "химиотерапия": ["опухоль", "лечение", "побочные эффекты", "протокол"]
    },
    "кардиолог": {
        "сердце": ["кардиология", "ЭКГ", "ЭХО", "аритмия", "давление"],
        "ЭКГ": ["сердце", "диагностика", "ритм", "электрическая активность"],
        "аритмия": ["сердце", "ритм", "диагноз", "лечение"]
    },
    "ветеринар": {
        "ветеринар": ["осмотр", "диагноз", "лечение", "профилактика", "вакцинация"],
        "осмотр": ["ветеринар", "диагноз", "симптомы", "анамнез"],
        "диагноз": ["ветеринар", "осмотр", "лечение", "анализы"],
        "лечение": ["ветеринар", "диагноз", "препараты", "протокол"]
    }
}

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None

def parse_site(html, url):
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return {
        "soup": soup,
        "text": text,
        "words": len(text.split()),
        "url": url,
        "sentences": [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    }

def extract_entities(text):
    entities = {}
    text_lower = text.lower()
    for topic_key, graph in REFERENCE_GRAPHS.items():
        if topic_key in text_lower:
            for entity, related in graph.items():
                if entity in text_lower:
                    contexts = []
                    for sentence in text.split('.'):
                        if entity in sentence.lower():
                            contexts.append(sentence.strip()[:100])
                    entities[entity] = {
                        "found": True,
                        "contexts": contexts[:3],
                        "related_expected": related
                    }
    return entities

def build_entity_graph(entities, sentences):
    graph = defaultdict(set)
    for sentence in sentences:
        sentence_lower = sentence.lower()
        found_entities = [e for e in entities.keys() if e in sentence_lower]
        for i, e1 in enumerate(found_entities):
            for e2 in found_entities[i+1:]:
                graph[e1].add(e2)
                graph[e2].add(e1)
    return {k: list(v) for k, v in graph.items()}

def compare_with_reference(built_graph, topic_key):
    if topic_key not in REFERENCE_GRAPHS:
        return {"score": 0, "missing_links": [], "extra_links": [], "coverage": "N/A"}
    ref_graph = REFERENCE_GRAPHS[topic_key]
    ref_normalized = defaultdict(set)
    for entity, related in ref_graph.items():
        for rel in related:
            ref_normalized[entity].add(rel)
            ref_normalized[rel].add(entity)
    total_expected = 0
    total_found = 0
    missing_links = []
    for entity, expected_related in ref_normalized.items():
        if entity in built_graph:
            actual_related = set(built_graph[entity])
            for rel in expected_related:
                total_expected += 1
                if rel in actual_related:
                    total_found += 1
                else:
                    missing_links.append(f"{entity} -> {rel}")
    score = int((total_found / total_expected * 100)) if total_expected > 0 else 0
    return {
        "score": min(100, score),
        "total_expected_links": total_expected,
        "total_found_links": total_found,
        "missing_links": missing_links[:10],
        "coverage": f"{total_found}/{total_expected}"
    }

def analyze_entity_centrality(built_graph):
    if not built_graph:
        return {"hubs": [], "isolated": [], "score": 0, "total_entities": 0, "avg_connections": 0}
    degrees = {entity: len(connections) for entity, connections in built_graph.items()}
    sorted_entities = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    hubs = [e[0] for e in sorted_entities[:3] if e[1] >= 2]
    isolated = [e for e, d in degrees.items() if d == 0]
    max_possible = len(degrees)
    hub_score = len(hubs) * 20
    isolation_penalty = len(isolated) * 10
    score = max(0, min(100, hub_score - isolation_penalty + 30))
    return {
        "hubs": hubs,
        "isolated": isolated,
        "total_entities": len(degrees),
        "avg_connections": round(sum(degrees.values()) / len(degrees), 1) if degrees else 0,
        "score": score
    }

def evaluate_link_quality(built_graph, sentences):
    if not built_graph:
        return {
            "score": 0,
            "natural_links": 0,
            "forced_links": 0,
            "total_links": 0,
            "natural_ratio": "0/0"
        }
    natural_count = 0
    forced_count = 0
    for entity, connections in built_graph.items():
        for connected in connections:
            found_natural = False
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if entity in sentence_lower and connected in sentence_lower:
                    pos1 = sentence_lower.find(entity)
                    pos2 = sentence_lower.find(connected)
                    if abs(pos1 - pos2) < 200:
                        found_natural = True
                        break
            if found_natural:
                natural_count += 1
            else:
                forced_count += 1
    total = natural_count + forced_count
    score = int((natural_count / total * 100)) if total > 0 else 0
    return {
        "score": score,
        "natural_links": natural_count,
        "forced_links": forced_count,
        "total_links": total,
        "natural_ratio": f"{natural_count}/{total}" if total > 0 else "0/0"
    }

def run_ai_audit_v5():
    print("="*70)
    print("АГЕНТ SEMANTIC GRAPH AUDIT v5: АНАЛИЗ ГРАФА СУЩНОСТЕЙ")
    print("="*70)
    sites = load_sites()
    registry = load_registry()
    site_topics = {}
    for topic in registry:
        site = topic.get("target_site", "")
        keyword = topic.get("primary_keyword", "")
        if site not in site_topics:
            site_topics[site] = []
        site_topics[site].append(keyword)
    print(f"Сайтов: {len(sites)} | Тем: {len(registry)}")
    results = []
    for key, cfg in sites.items():
        url = cfg.get('url')
        if not url:
            continue
        print(f"\n{'='*70}")
        print(f"Анализ: {key.upper()} ({url})")
        print(f"{'='*70}")
        html = fetch_html(url)
        if not html:
            print(f"  Ошибка загрузки {url}")
            continue
        parsed = parse_site(html, url)
        topic_keyword = site_topics.get(key, [""])[0] if site_topics.get(key) else ""
        topic_key = None
        for tk in REFERENCE_GRAPHS.keys():
            if tk in topic_keyword.lower():
                topic_key = tk
                break
        entities = extract_entities(parsed["text"])
        print(f"  Найдено сущностей: {len(entities)}")
        built_graph = build_entity_graph(entities, parsed["sentences"])
        total_links = sum(len(v) for v in built_graph.values()) // 2
        print(f"  Построено связей: {total_links}")
        if topic_key:
            comparison = compare_with_reference(built_graph, topic_key)
            print(f"  Покрытие эталонного графа: {comparison['coverage']} ({comparison['score']}%)")
            if comparison['missing_links']:
                print(f"  Недостающие связи: {', '.join(comparison['missing_links'][:5])}")
        else:
            comparison = {"score": 0, "missing_links": [], "coverage": "N/A"}
            print(f"  Эталонный граф не найден для темы '{topic_keyword}'")
        centrality = analyze_entity_centrality(built_graph)
        print(f"  Хабы графа: {', '.join(centrality['hubs']) if centrality['hubs'] else 'нет'}")
        print(f"  Изолированные: {', '.join(centrality['isolated']) if centrality['isolated'] else 'нет'}")
        print(f"  Оценка центральности: {centrality['score']}/100")
        link_quality = evaluate_link_quality(built_graph, parsed["sentences"])
        print(f"  Естественных связей: {link_quality['natural_ratio']}")
        print(f"  Оценка качества: {link_quality['score']}/100")
        scores_list = [comparison['score'], centrality['score'], link_quality['score']]
        total_score = sum(scores_list) // 3
        print(f"\n  ОБЩИЙ AI-СКОР v5: {total_score}/100")
        results.append({
            "site": key,
            "url": url,
            "topic": topic_keyword,
            "topic_key": topic_key,
            "entities_found": len(entities),
            "graph_comparison": comparison,
            "centrality": centrality,
            "link_quality": link_quality,
            "total_score": total_score,
            "built_graph": built_graph
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Semantic Graph Audit v5.0",
        "summary": {
            "avg_score": round(sum(r["total_score"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results),
            "reference_graphs_available": len(REFERENCE_GRAPHS)
        },
        "sites": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ SEMANTIC GRAPH AUDIT v5")
    print("="*70)
    print(f"Средний AI-скор v5: {report['summary']['avg_score']}/100")
    print(f"Проанализировано сайтов: {report['summary']['total_sites']}")
    print(f"Доступно эталонных графов: {report['summary']['reference_graphs_available']}")
    print(f"\nПолный отчёт с графами сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v5()
