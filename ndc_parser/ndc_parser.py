import re
import json
import copy
import codecs
from itertools import takewhile

def parse_ndc_ttl(ndc_editon: str, file):
    type_dict = {
        "Main": "類目（第1次区分）",
        "Division": "綱目（第2次区分）",
        "Section": "要目（第3次区分）",
        "Concept": "細目",
        "Variant": "二者択一項目",
        "Collection": "中間見出し・範囲項目",
    }

    top_item = {
        "type": "Top",
        "type@ja": "最上位",
        "edition": ndc_editon,
        "notation": "",
        "label@ja": None,
        "prefLabel@ja": None,
        "prefLabel@en": None,
        "indexedTerm@ja": [],
        "note@ja": [],
        "variantOf": None,
        "seeAlso": None,
        "related": [],
        "broader": None,
        "narrower": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        "source": [],
    }
    ndc_dict = {
        "": top_item
    }

    section_count = 0
    notations = []
    for line in file:
        if line.startswith("ndc" + ndc_editon + ":"):
            section_count += 1
            if section_count==1: # 1つ目は不要データなので飛ばす
                continue
            tmp_buff = [line]
            tmp_buff.extend(takewhile(lambda x: x.strip()!=".", file))
            # print("".join(tmp_buff))
            # print("---------------------------------------------")

            buff = []
            isIndexedTerm = False
            it_buff = []
            mr_buff = []
            for b in tmp_buff[1:]:
                b = re.sub(" ;$", "", b.strip())

                if b=="ndcv:indexedTerm [":
                    isIndexedTerm = True
                elif isIndexedTerm and b=="]":
                    isIndexedTerm = False
                elif isIndexedTerm:
                    it_buff.append(b)

                else:
                    buff.append(b)

            item = {}

            # 1行目の処理
            nm = re.search(r"ndcv:([^\s]+)", line)
            if nm:
                item["ndcv"] = nm.groups()[0].replace(",", "").strip()
            sm = re.search(r"skos:([^\s]+)", line)
            if sm:
                item["skos"] = sm.groups()[0].strip()

            def rm_quote(text):
                return re.sub(r"^\"|\"$", "",  text)

            # 各行処理
            for b in buff:
                if b=="rdfs:seeAlso [":
                    continue
                m = re.match(r"[^:]+:([^\s]+) (.+)", b)
                if m:
                    key = m.groups()[0]
                    value = m.groups()[1]
                    if key=="label":
                        lm = re.search(r"（?([^（）]+)）?", value)
                        if lm:
                            value = rm_quote(lm.groups()[0])
                    elif key=="prefLabel":
                        lm = re.search(r"(.*?)@ja", value)
                        if lm:
                            item["prefLabel@ja"] = rm_quote(lm.groups()[0])
                        lm = re.search(r", (.*?)@en", value)
                        if lm:
                            item["prefLabel@en"] = rm_quote(lm.groups()[0])
                    elif key=="notation":
                        value = rm_quote(value)
                    elif key=="broader":
                        value = value.split(":")[1]
                    elif key=="note":
                        value = [rm_quote(x.strip()) for x in value.split(",")]
                    elif key=="related" or key=="narrower":
                        value = [x.strip().split(':')[1] for x in value.split(",")]
                    item[key] = value

            # indexedTermの処理
            it_items = []
            temp_items = []
            for n in it_buff:
                m = re.match(r"[^:]+:([^\s]+) \"(.+)\"", n)
                if m:
                    temp_items.append(m.groups())
            it_item = []
            for temp_item in temp_items:
                if temp_item[0]=="literalForm":
                    it_item.append(temp_item[1]) 
                elif temp_item[0]=="transcription":
                    it_item.append(temp_item[1])
                    it_items.append(it_item)
                    it_item = []
            item["indexedTerm"] = it_items

               
            type_en = item["ndcv"] if "ndcv" in item else item["skos"]
            if type_en=="MainClass":
                type_en = "Main"
            if type_en!="Collection":
                notations.append(item["notation"])

            type_ja = type_dict[type_en]

            notation = item["notation"]
            if item["notation"] in top_item["narrower"]:
                item["broader"] = ""
            ndc_dict[item["notation"]] = {
                "type": type_en,
                "type@ja": type_ja,
                "edition": ndc_editon,
                "notation": notation,
                "label@ja": item["label"] if "label" in item else None,
                "prefLabel@ja": item["prefLabel@ja"] if "prefLabel@ja" in item else None,
                "prefLabel@en": item["prefLabel@en"] if "prefLabel@en" in item else None,
                "indexedTerm@ja": item["indexedTerm"],
                "note@ja": item["note"] if "note" in item else [],
                "variantOf": item["variantOf"] if "variantOf" in item else None,
                "seeAlso": item["seeAlso"] if "seeAlso" in item else None,
                "related": item["related"] if "related" in item else [],
                "broader": item["broader"] if "broader" in item else None,
                "narrower": item["narrower"] if "narrower" in item else [],
                "source": [re.sub(r"\t|\n", "", x) for x in tmp_buff],
            }

    return ndc_dict