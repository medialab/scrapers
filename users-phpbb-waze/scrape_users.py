#!/usr/bin/env python

import os, sys, json
import requests
import hashlib
from datetime import datetime
from pyquery import PyQuery as pq


COOKIE = "GCLB=CPjJxtjq1cLBqAE; phpbb3_waze_k=; phpbb3_waze_mobile=; __utma=23975868.1056868802.1546958877.1546958877.1546958877.1; __utmc=23975868; __utmz=23975868.1546958877.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _ga=GA1.2.1056868802.1546958877; _gid=GA1.2.852064896.1546958951; _csrf_token=s-4YnCuDXPJ1pCY4KCyfiQNpRWGdCFewwCP-C0wh6mQ; G_ENABLED_IDPS=google; _waze_session=dFI5MkdPRmoyMVhmN2JqZm5NOTExL0gxaHZsN1RtVFJWZUI1TXBNYklIMUhCendyc2R1OXZNbzhuL01pUS9lNGJ1NmRlNmJLNVFOWk1tY3FjbjF6d2UxQXlOWVIrRDNRQUJuWWdmRFo1a2h2Vy9YdG1tNy9VdmNxdDQ2QTczR2hRTVI5Q3hpUDh5WEY0eUl3aURCK3hnPT0tLWlENGZ3ZWVXdmpMYVpEa1RJazlPUUE9PQ%3D%3D--f76283cf983b1320695b1cbe36a9ec1f55343857; phpbb3_waze_u=17464168; phpbb3_waze_sid=7d7adbc73b3207634dcba555c1f9f531; __utmt=1; __utmb=23975868.35.10.1546958877; _web_session=eFVrZ01Wc21BZndnajVaT1ZLa09Lcm1NN3A5VmVGdG9HOEtFdFdxV29NYz0tLTZQeG1Md3Zra2R3OGNGK3FybG9aY1E9PQ%3D%3D--c65d88b4f98d1e07a680652619d682105b1c0f7a"
cookies = {c.split("=")[0]: c.split("=")[1] for c in COOKIE.split("; ")}

def datize(d):
    d = d.strip()
    if not d or d == "-":
        return ""
    return datetime.strptime(d[4:], "%b %d, %Y %I:%M %p").isoformat()[:10]


def download(url, retries=3):
    cache = os.path.join(".cache", hashlib.md5(url).hexdigest())
    if os.path.exists(cache) and os.path.getsize(cache):
        with open(cache) as f:
            return f.read()
    try:
        content = requests.get(url, cookies=cookies).text
        with open(cache, "w") as f:
            f.write(content.encode("utf-8"))
        return content
    except Exception as e:
        if retries:
            return download(url, retries - 1)
        print >> sys.stderr, "ERROR downloading %s" % url
        raise e


def parse_user_page(url):
    print "now processing", url
    content = download(url)
    jq = pq(content)
    key = None
    res = {}
    for line in jq(".bg1 .details, .bg2 .column2").text().split("\n"):
        if line.endswith(":"):
            key = line.rstrip(":")
        elif key:
            if key not in res:
                res[key] = line
            else:
                res[key] += "|" + line
    res["Joined"] = datize(res["Joined"])
    res["Last visited"] = datize(res["Last visited"])
    res["Age"] = int(res.get("Age", 0)) or ""
    res["Total posts"] = int(res["Total posts"].split("|")[0].strip())
    return res


def parse_list_page(start, posts_threshold=0):
    rooturl = "https://www.waze.com/forum/memberlist.php"
    baseurl = rooturl + "?sk=d&sd=d&start=%s"
    url = baseurl % start
    print "extracting users #%s to %s <%s>" % (start, start + 25, url)
    next_page = None
    users_pages = []
    content = download(url)
    jq = pq(content)
    for u in jq("#memberlist tbody tr"):
        tds = jq(u).find("td")
        if int(jq(tds[1]).text()) <= posts_threshold:
            continue
        user_url = jq(tds[0]).find("a").attr("href")
        user_url = user_url.replace("./memberlist.php", rooturl)
        users_pages.append(user_url)
    if users_pages:
        next_page = start + 25
    return users_pages, next_page


def format_for_csv(obj, key):
    if key not in obj:
        return ""
    if type(obj[key]) == int:
        return str(obj[key])
    if "," in obj[key]:
        return '"%s"' % obj[key].replace('"', '""')
    return obj[key]


def write_csv(data, filename, headers):
    with open(filename, "w") as f:
        print >> f, ",".join(headers)
        for row in data:
            print >> f, ",".join([format_for_csv(row, h).encode("utf-8") for h in headers])

if __name__ == "__main__":
    posts_threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    results = []
    next_page = 0
    users = True
    while users:
        users, next_page = parse_list_page(next_page, posts_threshold)
        results += [parse_user_page(u) for u in users]
    from pprint import pprint
    pprint(results)
    headers = ["Username", "Joined", "Last visited", "Rank", "Total posts", "Age", "Location", "Groups"]
    write_csv(results, "waze-forum-users.csv", headers)
    #pprint(parse_user_page("https://www.waze.com/forum/memberlist.php?mode=viewprofile&u=701618"))
    #with open("latimes_obituary_fu.json", "w") as f:
    #   json.dump(results, f)
