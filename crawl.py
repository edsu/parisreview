#!/usr/bin/env python

import re
import os
import sys
import json
import time
import pyld
import codecs
import rdflib
import urllib
import wplinks
import requests
import lxml.html

from rdflib import ConjunctiveGraph, URIRef, Literal, Namespace, RDF, RDFS
from rdflib.plugin import register, Parser, Serializer

register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')
register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')

parisreview = "http://www.theparisreview.org/interviews"
dcterms = Namespace("http://purl.org/dcterms/")
dbpedia = Namespace("http://dbpedia.org/ontology/")
bibo = Namespace("http://purl.org/ontology/bibo/")


def get_links():
    for w_url, pr_url in wplinks.extlinks(parisreview):
        m = re.match("https://.+/wiki/(.+)$", w_url)
        title = urllib.unquote(m.group(1).replace('_', ' '))
        if m and ':' not in title:
            G.add((URIRef(pr_url), dcterms.subject, URIRef(w_url)))
            G.add((URIRef(w_url), dcterms.title, Literal(title)))
    

def get_interviews():
    for decade in ('1950s', '1960s', '1970s', '1980s', '1990s', '2000s', '2010s'):
        url = 'http://www.theparisreview.org/interviews/' + decade
        doc = lxml.html.fromstring(requests.get(url).content)
        for a in doc.xpath('.//div[@class="archive-left-item"]/a'):
            get_interview(a.attrib['href'])


def get_interview(path):
    url = "http://www.theparisreview.org" + path
    html = requests.get(url).content.decode('utf8')
    doc = lxml.html.fromstring(html)
    title = doc.xpath('string(.//head/title)').split(" - ")[1]
    text = unicode(doc.xpath('string(.//div[@class="detail-interviews-description"])'))
    G.add((URIRef(url), RDF.type, bibo.Interview))
    G.add((URIRef(url), dcterms.title, Literal(title)))


def wikipedia_title(article_url):
    m = re.match("http://.+/wiki/(.+)$", article_url)
    t = None


def write():
    context = {
        "dcterms": dcterms,
        "dbpedia": dbpedia,
        "subject": {
            "@id": "dcterms:subject",
            "@container": "@set"
        },
        "title": {
            "@id": "dcterms:title"
        },
        "influencedBy": {
            "@id": "dbpedia:influencedBy",
            "@container": "@set"
        }
    }
    doc = json.loads(G.serialize(context=context, format="json-ld"))
    compacted = pyld.jsonld.compact(doc, context)

    json_data = json.dumps(compacted, indent=2)
    open("js/parisreview.json", "w").write(json_data)

    js = "var ParisReview = " + json_data + ";"
    open("js/parisreview.js", "w").write(js)


def get_influence_links():
    for wp_url in set(list(G.subjects())):
        m = re.match("https://en.wikipedia.org/wiki/(.+)", wp_url)
        if not m:
            continue
        title = m.group(1)
        dbpedia_url = URIRef('http://dbpedia.org/resource/%s' % title)
        dbp = ConjunctiveGraph()
        dbp.parse(dbpedia_url)

        for o in dbp.objects(dbpedia_url, dbpedia.influencedBy):
            m = re.match("http://dbpedia.org/resource/(.+)$", o)
            if not m: 
                continue
            wp_url2 = URIRef("https://en.wikipedia.org/wiki/" + m.group(1))
            if len(list(G.predicate_objects(wp_url2))) > 0:
                G.add((wp_url, dbpedia.influencedBy, wp_url2))


if __name__ == "__main__":
    G = rdflib.ConjunctiveGraph()
    print "getting interviews"
    get_interviews()
    print "getting links"
    get_links()
    print "getting influence links"
    get_influence_links()
    write()
