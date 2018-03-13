#!/usr/bin/env python

import os, sys
import requests
import hashlib
from pyquery import PyQuery as pq


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
    data = {
        "url": url,
        "name": jq("h1").text().split(",")[0],
        "picture": jq("img.homicide-photo").attr.src,
        "gender": "",
        "ethnicity": "",
        "agency": "",
        "age_at_death": "",
        "cause_of_death": "",
        "date_of_death": jq("img.homicide-photo").attr.title.split('(')[1].rstrip(')'),
        "geoloc": "",
        "adress": "",
        "city": "",
        "stories": [],
        "obituary": "\n".join([jq(p).text() for p in jq(".body p") if not jq(p).html().startswith("<em>")]),
        "obituary_date": jq(".post-date time").attr.datetime,
        "obituary_author_name": jq(".author a").text(),
        "obituary_author_email": jq(".author a").attr.href.split(":")[1],
        "comments": []
    }
    adress = []
    for li in jq(".hidden-phone .detail ul.aspects li"):
        litxt = jq(li).text()
        if ":" not in litxt:
            adress.append(litxt)
        else:
            val = litxt.split(":")[1]
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

    data["adress"] = "\n".join(adress[::-1])
    data["city"] = adress[0]
    nexturl = "http://homicide.latimes.com" + jq(".prev a").attr.href
    return data, nexturl


# TODO
# - handle geoloc from map
# - handle skip stories
# - handle comments

if __name__ == "__main__":
    if not os.path.exists(".cache"):
        os.makedirs(".cache")
    data, nexturl = parse_one("http://homicide.latimes.com/post/gabriel-fernandez/")
    from pprint import pprint
    pprint(data)
    print nexturl
