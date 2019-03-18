import json
import codecs
import zipfile
import responder
# from rdflib import Graph, plugin
# from rdflib.serializer import Serializer
# from pprint import pprint

api = responder.API()

# with zipfile.ZipFile('zips/ndc9.zip', 'r') as ndczip:
#     # print(ndczip.namelist())
#     ndc = ndczip.read('ndc9.ttl')

import re
from collections import namedtuple
from itertools import takewhile

def getNDCItems(ndc_name):
    items = []
    with codecs.open('zips/' + ndc_name + '.ttl', 'r', 'utf-8') as file:
        for line in file:
            if line.startswith(ndc_name + ':'):
                tmp_buff = [line]
                tmp_buff.extend(takewhile(lambda x: x.strip()!='.', file))
                # print(''.join(tmp_buff))
                # print('---------------------------------------------')

                # indexedTermだけbufferを分離
                buff = []
                isIndexedTerm = False
                it_buff = []
                for b in tmp_buff[1:]:
                    b = b.strip()
                    if b=='ndcv:indexedTerm [':
                        isIndexedTerm = True
                        it_buff.append(b)
                    elif b=='] ;':
                        isIndexedTerm = False
                        it_buff.append(b)
                    else:
                        if isIndexedTerm:
                            it_buff.append(b)
                            buff.append(b)
                
                item = {}

                # 1行目の処理 ex) ndc9:000 a ndcv:Section, skos:Concept ;
                ndm = re.search(r'ndc[8|9]:([^ndcv|skos]+)', line)
                if ndm:
                    item['ndc'] = ndm.groups()[0].strip()
                nm = re.search(r'ndcv:([^\s]+)', line)
                if nm:
                    item['ndcv'] = nm.groups()[0].replace(',', '').strip()
                sm = re.search(r'skos:([^\s]+)', line)
                if sm:
                    item['skos'] = sm.groups()[0].strip()

                # 各行処理
                for b in buff:
                    m = re.match(r'[^:]+:([^\s]+) ([^;]+) ;', b)
                    if m:
                        props = m.groups()
                        key = props[0]
                        value = props[1]
                        if key=='label' or key=='note':
                            lm = re.search(r'"([^"]+)"', value)
                            if lm:
                                value = lm.groups()[0].split('．')
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

                # indexedTermの処理
                for n in it_buff:
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
                    
                # print(item)
                items.append(item)
    return items

ndc8_items = getNDCItems('ndc8')
ndc9_items = getNDCItems('ndc9')

# f = codecs.open('zips/sample.ttl', 'r', 'utf-8')
# ndc = f.read()
# g = Graph().parse(data=ndc, format='n3')
# g = g.serialize(format='json-ld', indent=4)

@api.route("/")
def index(req, resp):
    resp.content = api.template('index.html')

@api.route("/ndc8")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc8_items[:100], ensure_ascii=False)

@api.route("/ndc9")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc9_items[:100], ensure_ascii=False)

if __name__ == '__main__':
    api.run()