#!/usr/bin/env python

import os, sys, json
import requests
import hashlib
from datetime import datetime
from pyquery import PyQuery as pq


datize = lambda dat: datetime.strptime("April 10, 2018", "%B %d, %Y").isoformat()[:10]


def download(url, retries=3):
	cache = os.path.join(".cache", hashlib.md5(url).hexdigest())
	if os.path.exists(cache) and os.path.getsize(cache):
		with open(cache) as f:
			return f.read()
	try:
		content = requests.get(url).text
		with open(cache, "w") as f:
			f.write(content.encode("utf-8"))
		return content
	except Exception as e:
		if retries:
			return download(url, retries - 1)
		print >> sys.stderr, "ERROR downloading %s" % url
		raise e


def parse_one(url,discover=False):
	print 'now processing ',url
	cache = os.path.join(".cache", hashlib.md5(url).hexdigest())
	goahead=True
	if os.path.exists(cache) and os.path.getsize(cache):
		if discover==False:
			goahead=False
			return None,None
	if goahead:
		content = download(url)
		jq = pq(content)
		nexturl = "http://homicide.latimes.com" + jq(".next a").attr.href
		data=None
		return data, nexturl


# TODO
# - add list of associated stories
# - handle comments
# - add multiproc from various starting points ?

if __name__ == "__main__":
	if not os.path.exists(".cache"):
		os.makedirs(".cache")
	if len(sys.argv) > 1:
		url = sys.argv[1]
		data, nexturl = parse_one(url)
		from pprint import pprint
		pprint(data)
		print nexturl
	else:
		#first prepare a list of see url to start crawling
		neighborhoods=[]
		feed=open('la_neigh_list.txt')
		for ligne in feed.readlines():
			neighborhoods.append(ligne[:-1])
		urlseeds=[]
		
		for neigh in neighborhoods[::-1]:
			for year in range(2000,2019)[::-1]:
					year_page="http://homicide.latimes.com/gender/female/" + "neighborhood/" + str(neigh) + '/'+"year/" + str(year) 
					print year_page
					content = download(year_page)
					jq = pq(content)			
					try:
						ass = jq("article h2")
						for a in str(ass).split('\n'):
							try:
								urlseeds.append("http://homicide.latimes.com" + str(ass('a')).split('<a href="')[1].split('">')[0])				
						
							except:
								pass
					except:
						pass
			
		print 'urlseeds',urlseeds
		results = []
		nexturl = "http://homicide.latimes.com/post/ommer-ganaway/"
		discovery=True
		while True:
			
			
			print 'nexturl',nexturl
			try:
				data, nexturl = parse_one(nexturl,discovery)
				discovery=False
				if nexturl==None:
					kdlqs
				results.append(data)
			except:
				nexturl=urlseeds[-1]
				print "\n\n***************\nstarting from a new seed url",nexturl
				urlseeds=urlseeds[:-1]
				discovery=True
		with open("results.json", "w") as f:
			json.dump(results, f)
