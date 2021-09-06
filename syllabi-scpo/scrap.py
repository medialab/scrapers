#!/usr/bin/env python

import os
import sys
import csv
import json
import time
import requests
from selectolax.parser import HTMLParser


CACHE = ".cache"


def init_cache(cachedir=CACHE):
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)


def download(url, retries=5, _json=False, cachedir=CACHE):
    cache = os.path.join(cachedir, url.replace(":", "_").replace("/", "_"))
    try:
        with open(cache) as f:
            if _json:
                return json.load(f)
            return f.read()
    except:
        try:
            r = requests.get(url)
            if _json:
                res = r.json()
                with open(cache, "w") as f:
                    json.dump(res, f)
                return res
            res = r.content.decode("utf-8")
            with open(cache, "w") as f:
                print(res, file=f)
            return res
        except:
            if retries:
                time.sleep(6-retries)
                return download(url, retries-1, _json=_json)
            print("ERROR: cannot access %s" % url, file=sys.stderr)


def scrape():
    syllabi = {}
    keys = ["ID", "URL", "Titre", "Langue"]

    translations = {
        "en": {
            "Course Description":   "Descriptif du cours",
            "Language of tuition":  "Langue d'enseignement",
            "Workload":             "Charge de travail",
            "Pre-requisite":        "Pré-requis",
            "Course validation":    "Mode de validation",
            "Pedagogical format":   "Format pédagogique",
            "Semester":             "Semestre",
            "Online materials":     "Support de cours en ligne"
        }, "es": {
            "Descriptivo del curso":    "Descriptif du cours",
            "Lengua de enseñanza":      "Langue d'enseignement",
            "Trabajo requerido":        "Charge de travail",
            "Condiciones previas":      "Pré-requis",
            "Validación":               "Mode de validation",
            "Formato pedagógico":       "Format pédagogique"
        }, "de": {
            "Veranstaltungsbeschreibung":   "Descriptif du cours",
            "Unterrichtssprache":           "Langue d'enseignement",
            "Arbeitsvolumen":               "Charge de travail",
            "Vorkenntnisse":                "Pré-requis",
            "Unterrichtsmodalitäten":       "Mode de validation",
            "Scheinerwerb":                 "Format pédagogique"
        }, "pt": {
            "Descrição do curso":   "Descriptif du cours",
            "Língua de ensino":     "Langue d'enseignement",
            "Carga de trabalho":    "Charge de travail",
            "Pré-requisito":        "Pré-requis",
            "Modo de validação":    "Mode de validation"
        }
    }

    titles = download("https://syllabus.sciencespo.fr/indexes/titles.js", _json=True)

    alphabet = map(chr, range(97, 123))
    for letter in alphabet:
        print("- WORKING ON LETTER %s..." % letter)
        catalogue_url = "https://syllabus.sciencespo.fr/indexes/%s.js" % letter
        catalogue = download(catalogue_url, _json=True)
        for keyword, ids_set in catalogue.items():
            for course_id, metadata in ids_set.items():
                if course_id in syllabi:
                    continue
                if len(metadata) < 2:
                    print("ERROR: missing metadata for course %s in keyword %s from %s" % (course_id, keyword, catalogue_url), file=sys.stderr)
                if metadata[0] != "e":
                    continue
                course_url = "https://syllabus.sciencespo.fr/cours/%s/%s.html" % (metadata[1], course_id)
                title = titles.get(course_id)
                if not title:
                    print("ERROR: missing course %s (%s) in titles for keyword %s with meta %s" % (course_id, course_url, keyword, metadata), file=sys.stderr)
                #print(" - COURSE %s: %s" % (title, course_url))
                content = download(course_url)
                tree = HTMLParser(content)
                title_bis = tree.css_first("h1").text()
                if title != title_bis:
                    print("WARNING: title is different in content (%s) than in metas (%s) for course %s %s" % (title_bis, title, course_id, course_url), file=sys.stderr)
                syllabi[course_id] = {
                    "ID": course_id,
                    "URL": course_url,
                    "Titre": title,
                    "Langue": "fr"
                }
                for div in tree.css(".cours > div"):
                    key = div.css_first("label").text().strip()
                    for lang in translations:
                        if key in translations[lang]:
                            key = translations[lang][key]
                            if syllabi[course_id]["Langue"] == "fr":
                                syllabi[course_id]["Langue"] = lang
                            break
                    if key not in keys:
                        keys.append(key)

                    value = div.css_first("div div").text().strip()
                    if key == "Enseignants":
                        value = value.replace(",", "|")
                    syllabi[course_id][key] = value

    return syllabi, keys


if __name__ == "__main__":
    init_cache()
    syllabi, keys = scrape()
    with open("syllabi.json", "w", encoding="utf-8") as f:
        json.dump(syllabi, f, ensure_ascii=False)
    with open("syllabi.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(keys)
        for course_id, values in syllabi.items():
            writer.writerow([values.get(k, "") for k in keys])
    print(keys)
