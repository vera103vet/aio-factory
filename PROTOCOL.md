# AIO-SYMPHONY: Standartny protokol raboty

**Versiya:** 1.0  
**Data sozdaniya:** 2026-10-08  
**Status:** Aktivny  
**Naznachenie:** Universalny algoritm generacii saytov s zashchitoy ot kannibalizacii i perespama

---

## NAZNACHENIE PROTOKOLA

Etot dokument opisivaet polny cikl raboty sistemy AIO-Symphony.

---

## VHODNYE DANNYE (ot zakazchika)

1. **Nazvanie sayta** (slug)
2. **Startovaya stranica** (starter.html)
3. **Stili** (styles.css)
4. **Kolichestvo stranic**

---

## ARHITEKTURA MASSHTABIROVANIYA

| Uroven | Tip | Stranic | Primer |
|--------|-----|---------|--------|
| 1 | Malye sayty-sputniki | ~60 | Dostoiny uhod |
| 2 | Srednie sayty | 150-500 | 18 tematicheskih saytov |
| 3 | Osnovnoy sayt | 1000-5000 | 103vet.by |

---

## ETAP 1: PLANIROVANIE

### Shag 1.1 - Site Structure Analyzer
**Agent:** agents/site_structure_analyzer.py

### Shag 1.2 - SEO Architect (Pervy strazh)
**Agent:** agents/seo_architect.py  
**Vyhod:** content_map_enriched.json

### Tochka sohraneniya #1
git add projects/{nazvanie}/ agents/seo_architect.py
git commit -m "feat: proekt {nazvanie} - plan kontenta"
git push origin main

---

## ETAP 2: GENERACIYA KONTENTA

### Shag 2.1 - Writer AI Pro v2.2
**Agent:** agents/adapter_writer_v2_2.py

### Shag 2.2 - Chief Editor v1.1
**Agent:** agents/chief_editor_v1_1.py

### Shag 2.3 - Critic v2.1
**Agent:** agents/domain_expert_critic_v2_1.py

### Tochka sohraneniya #2
git add data/sites/{nazvanie}/
git commit -m "feat: sgenerirovano stranic X iz N"
git push origin main

---

## ETAP 3: SVYAZYVANIE

### Shag 3.1 - Linker AI v5
**Agent:** agents/linker_ai_v5.py

---

## ETAP 4: KONTROL KACHESTVA

### Shag 4.1 - SEO Quality Auditor (Vtoroy strazh)
**Agent:** agents/seo_quality_auditor.py

### Shag 4.2 - 12 Lokalnyh auditorov

### Tochka sohraneniya #3
git add agents/seo_quality_auditor.py
git commit -m "feat: SEO Quality Auditor v1.0"
git push origin main

---

## ETAP 5: SBORKA

**Agent:** agents/team_production_assembly.py (v razrabotke)

---

## PROCEDURA VOSSTANOVLENIYA

1. Otkroy PROTOCOL.md
2. git log --oneline
3. Naydi posledniy rabochiy kommit
4. git checkout {hesh}
5. Prodolzi s nuzhnogo etapa
