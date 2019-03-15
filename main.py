import json
import codecs
import zipfile
import responder
from rdflib import Graph, plugin
from rdflib.serializer import Serializer
from pprint import pprint

api = responder.API()

# with zipfile.ZipFile('zips/ndc9.zip', 'r') as ndczip:
#     # print(ndczip.namelist())
#     ndc = ndczip.read('ndc9.ttl')

import re
from collections import namedtuple
from itertools import takewhile

items = []
with codecs.open('zips/sample.ttl', 'r', 'utf-8') as file:
    for line in file:
        if line.startswith('ndc9:'):
            print(line)
            buf = [line]
            buf.extend(takewhile(lambda x: x.strip()!='.', file))
            new_buf = []
            isNDCV = False
            ndcv_buf = []
            for b in buf[1:]:
                b = b.strip()
                if b=='ndcv:indexedTerm [':
                    isNDCV = True
                    ndcv_buf.append(b)
                elif b=='] ;':
                    isNDCV = False
                    ndcv_buf.append(b)
                else:
                    if isNDCV:
                        ndcv_buf.append(b)
                    else:
                        new_buf.append(b)
            # print(''.join(buf))
            # print('---------------------------------------------')
            
            item = {}

            # 1行目の処理 ex) ndc9:000 a ndcv:Section, skos:Concept ;
            ndm = re.search(r'(ndc[8|9]):([^ndcv|skos]+)', line)
            if ndm:
                item[ndm.groups()[0]] = ndm.groups()[1].strip()
            nm = re.search(r'ndcv:([^\s]+)', line)
            if nm:
                item['ndcv'] = nm.groups()[0].replace(',', '').strip()
            sm = re.search(r'skos:([^\s]+)', line)
            if sm:
                item['skos'] = sm.groups()[0].strip()

            for b in new_buf:
                m = re.match(r'[^:]+:([^\s]+) ([^;]+) ;', b)
                if m:
                    props = m.groups()
                    key = props[0]
                    value = props[1]
                    if key=='label' or key=='note':
                        lm = re.search(r'"([^"]+)"', value)
                        if lm:
                            value = lm.groups()[0]
                    if key=='prefLabel':
                        lm = re.search(r'"([^"]+)"@ja', value)
                        if lm:
                            item['prefLabel@ja'] = lm.groups()[0]
                        lm = re.search(r'"([^"]+)"@en', value)
                        if lm:
                            item['prefLabel@ja'] = lm.groups()[0]
                        continue
                    if key=='relatedMatch' or key=='seeAlso':
                        value = [x.strip() for x in value.split(',')]
                    item[key] = value
            for n in ndcv_buf:
                m = re.match(r'[^:]+:([^\s]+) ([^;]+) ;', n)
                if m:
                    ndvc_items = []
                    for ndvc_item in m.groups():
                        lm = re.search(r'"([^"]+)"', ndvc_item)
                        if lm:
                            ndvc_items.append(lm.groups()[0])
                        else:
                            ndvc_items.append(ndvc_item)
                    item['indexedTerm'] = ndvc_items
                
            print(item)
            items.append(item)

# f = codecs.open('zips/sample.ttl', 'r', 'utf-8')
# ndc = f.read()
# g = Graph().parse(data=ndc, format='n3')
# g = g.serialize(format='json-ld', indent=4)

@api.route("/")
def hello_world(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.media = items
    # resp.text = "hello, world2!"

if __name__ == '__main__':
    api.run()