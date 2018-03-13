#!/usr/bin/env python

import os, sys, json
import requests
import hashlib
from datetime import datetime
from pyquery import PyQuery as pq


datize = lambda dat: datetime.strptime("March 10, 2018", "%B %d, %Y").isoformat()[:10]


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


def parse_one(url):
    content = download(url)
    jq = pq(content)
    nexturl = "http://homicide.latimes.com" + jq(".prev a").attr.href
    details = jq(".hidden-phone .detail ul.aspects li")
    if not details:
        return None, nexturl
    img = jq("img.homicide-photo")
    author = jq(".author a")
    article = [p for p in jq(".body p") if jq(p).html()]
    data = {
        "id": jq(jq("script")[-8]).text().split('ids: [')[1].split(']')[0],
        "url": url,
        "name": jq("h1").text().split(",")[0],
        "picture": img.attr.src if img else None,
        "gender": None,
        "ethnicity": None,
        "agency": None,
        "age_at_death": None,
        "cause_of_death": None,
        "date_of_death": img.attr.title.split('(')[1].rstrip(')') if img else datize(jq(".death-date").text()),
        "geoloc": None,
        "adress": None,
        "city": None,
        "stories": [],
        "obituary": "\n".join([jq(p).text() for p in article if not jq(p).html().startswith("<em>")]),
        "obituary_date": jq(".post-date time").attr.datetime,
        "obituary_author_name": author.text() if author else None,
        "obituary_author_email": author.attr.href.split(":")[1] if author else None,
        "comments": []
    }
    adress = []
    for li in details:
        litxt = jq(li).text()
        if ":" not in litxt:
            adress.append(litxt)
        else:
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
    geojson = download("http://homicide.latimes.com/api/homicide.geojson?id=%s&permissive=True" % data["id"])
    if geojson:
        data["geoloc"] = {}
        data["geoloc"]["long"], data["geoloc"]["lat"] = json.loads(geojson)["geojson"]["features"][0]["geometry"]["coordinates"]
    if adress:
        data["adress"] = "\n".join(adress[::-1])
        data["city"] = adress[0]
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
        results = []
        nexturl = "http://homicide.latimes.com/post/daniel-anthony-sanchez/"
        while nexturl:
            print nexturl
            data, nexturl = parse_one(nexturl)
            results.append(data)
        with open("results.json", "w") as f:
            json.dump(results, f)
