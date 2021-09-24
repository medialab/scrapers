# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
from bs4 import BeautifulSoup
from bs4 import CData
import lxml

folder = sys.argv[1]

output = csv.writer(sys.stdout)
# liste des entêtes de colonnes a insérer dans le csv
headers = [
    "Code",
    "Semestre",
    "Titre",
    "Description",
    "Langue"
]
output.writerow(headers)

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

def get_text(x):
    if type(x) == str:
        return x
    return x.text

def parser(balise, soup=None, attrs=None, multivaleurpointvirgule=False, extra_balise=None, extra_data=None):
    # je cherche la balise dans la soupe (le fichier xml)
    champ = soup.find_all(balise, attrs=attrs)
    if extra_balise:
        champ += soup.find_all(extra_balise, attrs=attrs)
    if extra_data:
        champ.append(extra_data)
    if multivaleurpointvirgule == True:
        champ = '|'.join(['|'.join([y.strip() for y in get_text(x).split(';')]) for x in champ])
    else:
        champ = '|'.join(t for t in [get_text(x).strip() for x in champ] if t)
    return champ.strip()

for xmlfile in os.listdir(folder):
    xmlpath = os.path.join(folder, xmlfile)
    xml = open(xmlpath, 'r').read()
    sp = BeautifulSoup(xml, 'lxml')

    for course in sp.find_all("crse"):
        line_csv = []
        line_csv.append("%s %s" % (parser("subj", soup=course), parser("crse_nb", soup=course)))
        line_csv.append(parser("sem_l", soup=course))
        line_csv.append(parser("title", soup=course))
        line_csv.append(parser("desc", soup=course))
        descr_key = parser("edesc", soup=course)
        for lang in translations:
            if descr_key in translations[lang]:
                line_csv.append(lang)
                break

        output.writerow(line_csv)
