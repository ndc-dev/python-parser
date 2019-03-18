import json
import copy
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

def get_ndc_items(ndc_name):
    items = []
    with codecs.open('zips/' + ndc_name + '.ttl', 'r', 'utf-8') as file:
        section_count = 0
        for line in file:
            if line.startswith(ndc_name + ':'):
                section_count += 1
                if section_count==1: # トップは不要データなので飛ばす
                    continue
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
                        else:
                            buff.append(b)
                
                item = {}

                # 1行目の処理 ex) ndc9:000 a ndcv:Section, skos:Concept ;
                ndm = re.search(r'ndc[8|9]:([^ndcv|skos]+)', line)
                if ndm:
                    item['ndc'] = ndm.groups()[0].strip().split(' ')[0] # 000 a の a を削除
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
                        if key=='label' or key=='note' or key=='notation':
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
                # if section_count > 2:
                #     break
    return items


def get_category_number(ndc):
    return ndc.split(' ')[0].split('.')[0].split('_')[0] # 071_07 対策

def get_parallel_labels(items):
    parallel_labels = {}
    for item in items:
        category_number = get_category_number(item['ndc'])
        if category_number not in parallel_labels:
            parallel_labels[category_number] = [item['ndc']]
        else:
            parallel_labels[category_number].append(item['ndc'])
    return parallel_labels

def get_items(ndc):
    items = get_ndc_items(ndc)
    parallel_labls = get_parallel_labels(items)
    items_dict = {}
    for item in items:
        category_number = get_category_number(item['ndc'])
        if len(category_number)<=2:
            items_dict[category_number] = {
                'ndc': item['ndc'],
                'label': item['label'] if 'label' in item else ''
            }
    for item in items:
        category_number = get_category_number(item['ndc'])
        item['paralell_labels'] = []
        item['upper_level_labels'] = []
        if category_number in parallel_labls:
            parallel_labels = parallel_labls[category_number]
            item['paralell_labels'] = [label for label in parallel_labels if label != item['ndc']]
        item['upper_level_labels'] = []
        while len(category_number)>1:
            category_number = category_number[:-1]
            item['upper_level_labels'].append(items_dict[category_number])
    return items

ndc8_items = get_items('ndc8')
ndc9_items = get_items('ndc9')

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

@api.route("/ndc8_labels")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc8_parallel_labls, ensure_ascii=False)


@api.route("/ndc9")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc9_items[:100], ensure_ascii=False)

@api.route("/ndc9_labels")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc9_parallel_labls, ensure_ascii=False)


if __name__ == '__main__':
    api.run()