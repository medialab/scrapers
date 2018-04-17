#!/usr/bin/env python

import os, sys, json
import requests
import hashlib
from datetime import datetime
from pyquery import PyQuery as pq
import time

#datize = lambda dat: datetime.strptime("April 10, 2018", "%B %d, %Y").isoformat()[:10]


neighborhoods=[]
feed=open('la_neigh_list.txt')
for ligne in feed.readlines():
	neighborhoods.append(ligne[:-1])

conv_from=time.strptime('Feb 01 2010',"%b %d %Y")
conv_until=time.strptime('Dec 31 2016',"%b %d %Y")

def parse_one(url):
	print 'now processing ',url
	with open(url) as f:
		content= f.read()
	jq = pq(content)
	#nexturl = "http://homicide.latimes.com" + jq(".prev a").attr.href
	#data=None
	details = jq(".hidden-phone .detail ul.aspects li")
	if not details:
		return None
	img = jq("img.homicide-photo")
	url = jq("meta[property='og:url']").attr('content')
	author = jq(".author a")
	article = [p for p in jq(".body p") if jq(p).html()]
	comments = [comm for comm in jq(".django-comment")]
	comment_text=[]
	for comm in comments:
		commentt= str(jq(comm)('p'))
		#print commentt
		commentt=commentt.replace('<br/>','\n')
		commentt=commentt.replace('<p>','')
		commentt=commentt.replace('</p>','\n')
		commentt=commentt.replace("<p/>",'\n')
		commentt=commentt.replace("\n\n",'\n')
		commentt=commentt.replace("\n\n",'\n')
		commentt=commentt.replace("\n\n",'\n')
		commentt=commentt.replace("\n\n",'\n')
		commentt=commentt.replace("\n        ",'')
		comment_text.append(commentt)
	commentsname = [comm.text for comm in jq(".django-comment span .quote-name")]
	commentsdate = [comm.text for comm in jq(".django-comment span .quote-timestamp")]
	commentsdates=[]
	commentshours=[]
	#print len(comments),len(commentsname)
	for cda in commentsdate:
		cdav=cda.split()
		cdam=cdav[0][:3]
		cdad=cdav[1][:-1]
		cday=cdav[2]
		cdah=' '.join(cdav[3:4])
		#print cdam + ' ' + cdad + ' '+cday
		conv=time.strptime(cdam + ' ' + cdad + ' '+cday,"%b %d %Y")
		commentsdates.append(time.strftime("%Y-%m-%d",conv))
		commentshours.append(cdah)

	[dm,dd,dy] =jq(".death-date").text().split()[:3]
	#print dm,dd,dy
	#print dy +'-'+ dm[:3]+'-'+dd[:2]
	dd=dd.split(',')[0]
	conv=time.strptime(dm[:3]+' '+dd+' '+dy,"%b %d %Y")
	
	#print datedeath
	#print "commentsdate",commentsdate
	data = {
		"nb_comments":len(comments),
		"id": jq(jq("script")[-8]).text().split('ids: [')[1].split(']')[0],
		"url": url,
		"name": jq("h1").text().split(",")[0],
		"picture": img.attr.src if img else None,
		"gender": None,
		"ethnicity": None,
		"agency": None,
		"age_at_death": None,
		"cause_of_death": None,
		"date_of_death": conv,
		"adress": None,
		"neighborhood": None,
		"stories": [],
		"obituary": "\n".join([jq(p).text() for p in article if not jq(p).html().startswith("<em>")]),
		"obituary_date": jq(".post-date time").attr.datetime,
		"comments": comment_text,
		"commenters": commentsname,
		"commentdates": commentsdates,
		"commenthours": commentshours,
		"commentoriginaldate": commentsdate,
		"officer_involved": 'No Officer Involved',
		
	}	
	adress = []
	for li in details:
		litxt = jq(li).text()
		if ":" not in litxt:
			if 'Officer-involved' in litxt:
				data['officer_involved']='Officer Involved'
			else:
				adress.append(litxt)
		else:
			#print litxt
			val = litxt.split(":")[1].strip()
			field = None
			for key, fld in [
				("Age:", "age_at_death"),
				("Gender:", "gender"),
				("Cause:", "cause_of_death"),
				("Race/Ethnicity:", "ethnicity"),
				("Agency:", "agency")
			]:
				if key in litxt:
					field = fld
			if not field:
				print >> sys.stderr, "WARNING: unknown field found: %s in %s" % (litxt, url)
			else:
				data[field] = val
	if adress:
		data["adress"] = "\n".join(adress[::-1])
		#if adress[0] in neighborhoods:
		try:
			print int(adress[0].split()[0])
			data["neighborhood"] = 'unknown'
		except:
			data["neighborhood"] = adress[0]
			
	return data



if __name__ == "__main__":
	results = []
	results_comm = []
	files= map(lambda x: os.path.join('.cache',x),os.listdir('.cache'))
	#files=['.cache/aec766b226f083e5fa4bee27976fe1ba']
	j=0
	for file in files[:]:
		data = parse_one(file)
		
		if not data ==None:
			
			if data['date_of_death']>=conv_from and data['date_of_death']<=conv_until: 
				data['date_of_death']=time.strftime("%Y-%m-%d",data['date_of_death'])
				i=0
				for comm,commauthor,commdate,commoridate in zip(data['comments'],data['commenters'],data['commentdates'],data['commentoriginaldate']):
					j+=1
					temp={}
					temp['id_comment']=j
					temp['comment']=comm.replace('&amp;','&')
					temp['comment_order']=len(data['comments'])-i
					temp['author']=commauthor
					temp['date']=commdate
					temp['date_of_death']=	data['date_of_death']
					temp['date_ori']=commoridate
					temp['url']=data['url']
					temp['name']=data['name']
					temp['gender']=data['gender']
					temp['ethnicity']=data['ethnicity']
					temp["age_at_death"]=data["age_at_death"]
					temp['neighborhood']=data['neighborhood']
					temp["cause_of_death"]=data["cause_of_death"]
					temp['officer_involved']=data['officer_involved']
					i+=1
					results_comm.append(temp)
				results.append(data)
			else:
				pass
	with open("latimes_obituary_fu.json", "w") as f:
		json.dump(results, f)
	with open("latimes_comments_fu.json", "w") as f:
		json.dump(results_comm, f)
