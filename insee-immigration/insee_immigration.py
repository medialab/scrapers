#!/usr/bin/env python
# -*- coding: utf8 -*-

import re
import csv
import time
import random
import urllib2
from lxml import etree
from pyquery import PyQuery as pq

random.seed()

# URL bases for the INSEE pages to scrrrrap
bases_url = {
	"immigration_2009" : "https://www.insee.fr/fr/statistiques/2044109?sommaire=2131811&geo=DEP-",
	"immigration_2014" : "https://www.insee.fr/fr/statistiques/2874034?sommaire=2874056&geo=DEP-",
	"nationalite_2009" : "https://www.insee.fr/fr/statistiques/2044123?sommaire=2131811&geo=DEP-",
	"nationalite_2014" : "https://www.insee.fr/fr/statistiques/2874048?sommaire=2874056&geo=DEP-",
}

# Creates a csv file for each page, adds in headers
csv_outputs = {}
for base in bases_url:
	csv_output = csv.writer(open(base + ".csv", 'w'))
	if "immigration" in base:
		csv_output.writerow(["Département", "", "Immigrés", "Non-immigrés", "Ensemble" ])
	else:
		csv_output.writerow(["Département", "", "Français", "Étrangers", "Ensemble" ])
	csv_outputs[base] = csv_output

# Loops over the 95 departments of France
for departement in range(1, 96):
	departement = str(departement).zfill(2)
	print("Doing le departement {}".format(departement))

	# For each department gets the different infos
	for base in bases_url:
		# Builds full url with department
		url = bases_url[base] + departement
		# Jquery the page
		page = pq(url=url)
		# Finds the one table we want in the page (depends on type of base URL)
		if "immigration" in base :
			table = page('#produit-tableau-IMG1A_ENS')
		else:
			table = page('#produit-tableau-NAT1_V1_ENS')
		# Get the rows of the table
		rows = table('tr')
		# Starts building the output csv line
		line = [departement]

		for tr in rows:
			# Each row to a jquery object
			tr = pq(etree.tostring(tr))
			# Get the actual number from the row
			cell_data = tr('td:nth-child(6)').text().encode('utf8').replace(' ', '')
			# Append the row to the output line
			line.append(cell_data)

		# Write the results in the right csv, sleeps, output whatever in the console
		csv_outputs[base].writerow(line)
		night = random.random()
		time.sleep(night)
		print("Did {} and slept for {}".format(base, str(round(night, 2))))
	print('---')