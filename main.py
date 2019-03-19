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
        notations = []
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
                isStructuredLabel = False
                sl_buff = []
                isIndexedTerm = False
                it_buff = []
                isMemberRange = False
                mr_buff = []
                for b in tmp_buff[1:]:
                    b = b.strip()
                    if b=='ndcv:structuredLabel [':
                        isStructuredLabel = True
                    elif isStructuredLabel and b=='] ;':
                        isStructuredLabel = False
                    elif b=='ndcv:indexedTerm [':
                        isIndexedTerm = True
                    elif isIndexedTerm and b=='] ;':
                        isIndexedTerm = False
                    elif b=='ndcv:memberRange [':
                        isMemberRange = True
                    elif isMemberRange and b==']':
                        isMemberRange = False
                    elif isIndexedTerm:
                        it_buff.append(b)
                    elif isMemberRange:
                        mr_buff.append(b)
                    else:
                        buff.append(b)

                item = {}

                # 1行目の処理 ex) ndc9:000 a ndcv:Section, skos:Concept ;
                # ndm = re.search(r'ndc[8|9]:([^ndcv|skos]+)', line)
                # if ndm:
                #     item['ndc'] = ndm.groups()[0].strip().split(' ')[0] # 000 a の a を削除
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
                        if key=='label':
                            lm = re.search(r'"?（?([^"（）]+)）??"', value)
                            if lm:
                                value = lm.groups()[0].split('．')
                        if key=='prefLabel':
                            lm = re.search(r'"（?([^"（）]+)）?"@(en|ja)', value)
                            if lm:
                                if lm.groups()[1]=='ja':
                                    item['prefLabel@ja'] = lm.groups()[0].split('．')
                                if lm.groups()[1]=='en':
                                    item['prefLabel@en'] = lm.groups()[0].split('．')
                            continue
                        if key=='note':
                            lm = re.search(r'"?([^"]+)?"', value)
                            if lm:
                                value = lm.groups()[0]
                        if key=='notation':
                            lm = re.search(r'"?([^"]+)?"', value)
                            if lm:
                                value = lm.groups()[0]
                        if key=='relatedMatch' or key=='seeAlso':
                            value = [x.strip() for x in value.split(',')]
                        item[key] = value

                def getData(buff):
                    items = []
                    temp_items = []
                    for n in buff:
                        m = re.match(r'[^:]+:([^\s]+) "([^;]+)" ?;?', n)
                        if m:
                            temp_items.append(m.groups())
                    
                    item = []
                    for temp_item in temp_items:
                        if temp_item[0]=='literalForm':
                            item.append(temp_item[1]) 
                        elif temp_item[0]=='transcription':
                            item.append(temp_item[1])
                            items.append(item)
                            item = []
                    return items
                # structuredLabelの処理
                item['structuredLabel'] = getData(sl_buff)
                # indexedTermの処理
                item['indexedTerm'] = getData(it_buff)

                # memberRangeの処理
                item['memberRange'] = {}
                for n in mr_buff:
                    # xsd:minInclusive 930.25 ;
                    m = re.match(r'[^:]+:([^\s]+) ([^\s;]+) ?;?', n)
                    if m:
                        print(n)
                        print(m.groups())
                        item['memberRange'][m.groups()[0]] = m.groups()[1]
                    
                # print(item)
                # type  [String]
                # 　分類項目の種類（英語） Top,Main,Division,Section,Concept,Variant,Collection
                # type@ja   [String]
                # 　分類項目の種類（日本語） 最上位,類目（第1次区分）,綱目（第2次区分）,要目（第3次区分）,細目,二者択一項目,中間見出し・範囲項目
                # scheme [String]
                # 　NDCの版次   8,9
                # notation [Array of String]
                # 　分類記号 ・・・範囲がある場合は複数になる場合がある
                # label@ja [ Array of String ]
                # prefLabel@en [String]
                # prefLabel@ja [String]
                # indexedTerm@ja [Array of Array] 索引語 [(索引,索引の読み),(索引,索引の読み)]
                # note@ja [Array of String] 
                # variantOf [String or null]
                # seeAlso [Array of String]　分類記号のリスト
                # related [Array of String]　分類記号のリスト
                # broader [Array of String]　分類記号のリスト
                # narrower[Array of String]　分類記号のリスト


                # print(item)
                type_en = item['ndcv'] if 'ndcv' in item else item['skos']
                if type_en=='MainClass':
                    type_en = 'Main'
                type_ja = {
                    'Main': '類目（第1次区分）',
                    'Division': '綱目（第2次区分）',
                    'Section': '要目（第3次区分）',
                    'Concept': '細目',
                    'Variant': '二者択一項目',
                    'Collection': '中間見出し・範囲項目',
                }
                notations.append(item['notation'])
                notation = [item['notation']]
                if 'memberRange' in item:
                    notation = item['memberRange']
                items.append({
                    'type': type_en,
                    'type@ja': type_ja[type_en],
                    'scheme': item['inScheme'],
                    'notation': notation,
                    'label@ja': item['label'] if 'label' in item else [],
                    'prefLabel@ja': item['prefLabel@ja'] if 'prefLabel@ja' in item else [],
                    'prefLabel@en': item['prefLabel@en'] if 'prefLabel@en' in item else [],
                    'indexedTerm@ja': item['indexedTerm'],
                    'note@ja': item['note'] if 'note' in item else '',
                    'variantOf': item['variantOf'] if 'variantOf' in item else None,
                    'seeAlso': item['seeAlso'] if 'seeAlso' in item else [],
                    'related': item['related'] if 'related' in item else [],
                    'broader': item['broader'] if 'broader' in item else '',
                    'narrower': item['narrower'] if 'narrower' in item else '',
                })
                # if section_count > 2:
                #     break

    # 中間見出し・範囲項目のnotationを復元する
    for item in items:
        # 中間見出し・範囲項目
        if item['type']=='Collection':
            print(item)
            range_notations = []
            is_range = False
            for notation in notations:
                if notation==item['notation']['minInclusive']:
                    is_range = True
                    range_notations.append(notation)
                elif notation==item['notation']['maxExclusive']:
                    is_range = False
                    range_notations.append(notation)
                    break
                else:
                    if is_range:
                        range_notations.append(notation)
            item['notation'] = range_notations        
    return items


def get_category_number(notation):
    return notation.split(' ')[0].split('.')[0].split('/')[0] # 071/07 対策

# def get_parallel_labels(items):
#     parallel_labels = {}
#     for item in items:
#         if len(item['notation']) == 1:
#             category_number = get_category_number(item['notation'][0])
#             if category_number not in parallel_labels:
#                 parallel_labels[category_number] = [item['notation'][0]]
#             else:
#                 parallel_labels[category_number].append(item['notation'][0])
#     return parallel_labels


# def get_items(ndc):
    # parallel_labls = get_parallel_labels(items)
    # items_dict = {}
    # for item in items:
    #     if len(item['notation']) == 1:
    #         category_number = get_category_number(item['notation'][0])
    #         if len(category_number)<=2:
    #             items_dict[category_number] = {
    #                 'notation': item['notation'],
    #                 'label@ja': item['label@ja'] if 'label@ja' in item else ''
    #             }
    # for item in items:
    #     if len(item['notation']) == 1:
    #         category_number = get_category_number(item['notation'][0])
    #         item['paralell'] = []
    #         item['up'] = []
    #         if category_number in parallel_labls:
    #             parallel_labels = parallel_labls[category_number]
    #             item['paralell'] = [label for label in parallel_labels if label != item['notation']]
    #         item['up'] = []
    #         while len(category_number)>1:
    #             category_number = category_number[:-1]
    #             item['up'].append(items_dict[category_number])
    # return items

ndc8_items = get_ndc_items('ndc8')
ndc9_items = get_ndc_items('ndc9')

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
    resp.content = json.dumps(ndc8_items[:1000], ensure_ascii=False)

@api.route("/ndc8_labels")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc8_parallel_labls, ensure_ascii=False)


@api.route("/ndc9")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc9_items[:1000], ensure_ascii=False)

@api.route("/ndc9_labels")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc9_parallel_labls, ensure_ascii=False)


if __name__ == '__main__':
    api.run()