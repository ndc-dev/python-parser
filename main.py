import re
import json
import copy
import codecs
import io
import zipfile
import responder
api = responder.API()
from itertools import takewhile

def parse_ndc_ttl(ndc_name, file):
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
        "scheme": ndc_name+":",
        "notation": [],
        "label@ja": [],
        "prefLabel@ja": [],
        "prefLabel@en": [],
        "indexedTerm@ja": [],
        "note@ja": None,
        "variantOf": None,
        "seeAlso": [],
        "related": [],
        "broader": [],
        "narrower": [],
    }
    items = [top_item]

    section_count = 0
    notations = []
    for line in file:
        if line.startswith(ndc_name + ":"):
            section_count += 1
            if section_count==1: # トップは不要データなので飛ばす
                continue
            tmp_buff = [line]
            tmp_buff.extend(takewhile(lambda x: x.strip()!=".", file))
            # print("".join(tmp_buff))
            # print("---------------------------------------------")

            buff = []
            isIndexedTerm = False
            it_buff = []
            isMemberRange = False
            mr_buff = []
            for b in tmp_buff[1:]:
                b = b.strip()

                if b=="ndcv:indexedTerm [":
                    isIndexedTerm = True
                elif isIndexedTerm and b=="] ;":
                    isIndexedTerm = False
                elif isIndexedTerm:
                    it_buff.append(b)

                elif b=="ndcv:memberRange [":
                    isMemberRange = True
                elif isMemberRange and b=="]":
                    isMemberRange = False
                elif isMemberRange:
                    mr_buff.append(b)

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
                m = re.match(r"[^:]+:([^\s]+) ([^;]+) ;", b)
                if m:
                    key = m.groups()[0]
                    value = m.groups()[1]
                    if key=="label":
                        lm = re.search(r"（?([^（）]+)）?", value)
                        if lm:
                            value = rm_quote(lm.groups()[0]).split("．")
                    if key=="prefLabel":
                        lm = re.search(r"(.*?)@ja", value)
                        if lm:
                            item["prefLabel@ja"] = rm_quote(lm.groups()[0]).split("．")
                        lm = re.search(r"(.*?)@en", value)
                        if lm:
                            item["prefLabel@en"] = rm_quote(lm.groups()[0]).split(".")
                        continue
                    if key=="note" or key=="notation":
                        value = rm_quote(value)
                    if key=="seeAlso" or key=="related" or key=="broader" or key=="narrower":
                        value = [x.strip().split(':')[1] for x in value.split(",")]
                    item[key] = value

            # indexedTermの処理                
            it_items = []
            temp_items = []
            for n in it_buff:
                m = re.match(r"[^:]+:([^\s]+) \"([^;]+)\" ?;?", n)
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

            # memberRangeの処理
            item["memberRange"] = {}
            for n in mr_buff:
                # xsd:minInclusive 930.25 ;
                m = re.match(r"[^:]+:([^\s]+) ([^\s;]+) ?;?", n)
                if m:
                    item["memberRange"][m.groups()[0]] = m.groups()[1]
                
            type_en = item["ndcv"] if "ndcv" in item else item["skos"]
            if type_en=="MainClass":
                type_en = "Main"
            if type_en!="Collection":
                notations.append(item["notation"])

            type_ja = type_dict[type_en]

            notation = None
            if "notation" in item:
                notation = [item["notation"]]
            if len(item["memberRange"]) > 0:
                notation = item["memberRange"]

            items.append({
                "type": type_en,
                "type@ja": type_ja,
                "scheme": item["inScheme"],
                "notation": notation,
                "label@ja": item["label"] if "label" in item else [],
                "prefLabel@ja": item["prefLabel@ja"] if "prefLabel@ja" in item else [],
                "prefLabel@en": item["prefLabel@en"] if "prefLabel@en" in item else [],
                "indexedTerm@ja": item["indexedTerm"],
                "note@ja": item["note"] if "note" in item else None,
                "variantOf": item["variantOf"] if "variantOf" in item else None,
                "seeAlso": item["seeAlso"] if "seeAlso" in item else [],
                "related": item["related"] if "related" in item else [],
                "broader": item["broader"] if "broader" in item else [],
                "narrower": item["narrower"] if "narrower" in item else [],
            })

    def get_range_notations(min, max):
        def get_float(notation):
            return float(notation.split('/')[0])
        range_notations = []
        is_range = False
        for notation in notations:
            if notation==min:
                is_range = True
                range_notations.append(notation)
            elif get_float(notation) > get_float(max):
                is_range = False
            else:
                if is_range:
                    range_notations.append(notation)
        return range_notations

    # 中間見出し・範囲項目、seeAlsoのnotationを復元する
    for item in items:
        # 中間見出し・範囲項目
        if item["type"]=="Collection":
            item["notation"] = get_range_notations(item["notation"]["minInclusive"], item["notation"]["maxExclusive"])
        if 'seeAlso' in item and len(item['seeAlso'])>0:
            for see_also in item['seeAlso']:
                see_alsos = []
                if re.search(r'_', see_also):
                    range_see_alsos = get_range_notations(see_also.split('_')[0], see_also.split('_')[1])
                    see_alsos.extend(range_see_alsos)
                else:
                    see_alsos.append(see_also)
            item['seeAlso'] = see_alsos
    return items





def get_parallel_labels(items):
    parallel_labels = {}
    for item in items:
        if len(item["notation"]) == 1:
            category_number = get_category_number(item["notation"][0])
            if category_number not in parallel_labels:
                parallel_labels[category_number] = [item["notation"][0]]
            else:
                parallel_labels[category_number].append(item["notation"][0])
    return parallel_labels

    # parallel_labls = get_parallel_labels(items)
            # item["paralell"] = []
            # if category_number in parallel_labls:
            #     parallel_labels = parallel_labls[category_number]
            #     item["paralell"] = [label for label in parallel_labels if label != item["notation"]]
    # def get_category_number(notation):
    #     return notation.split(" ")[0].split(".")[0].split("/")[0] # 071/07 対策



ndc_dict = {}
down_dict = {}
def add_relate_ndc(items):
    # NDCでひける辞書を作る
    for item in items:
        if len(item["notation"]) == 1:
            ndc_dict[item["notation"][0]] = {
                "notation": item["notation"],
                "label@ja": item["label@ja"] if "label@ja" in item else ""
            }
            down_dict[item["notation"][0]] = []
    for item in items:
        if len(item["notation"]) == 1:
            ndc = item["notation"][0]
            item["up"] = []
            item['down'] = []
            while len(ndc)>1:
                ndc = ndc[:-1]
                ndc = re.sub(r"\.$", "", ndc)
                if ndc in ndc_dict:
                    item["up"].append(ndc_dict[ndc])
                if ndc in down_dict:
                    if len(item["notation"][0].replace(".", "")) == (len(ndc.replace(".", "")) + 1):
                        down_dict[ndc].append({
                            "notation": item["notation"],
                            "label@ja": item["label@ja"] if "label@ja" in item else ""
                        })
    for item in items:
        if len(item["notation"]) == 1:
            item['down'] = down_dict[item["notation"][0]]
    # for item in items:
    #     if len(item["notation"]) == 1:
    #         if len(item["up"]) >0:
    #             print(item["up"][0]["notation"])
    #             print(down_dict[item["up"][0]["notation"]])
                # item["contain"] = down_dict[item['up'][0]]["down"]
    return items



with zipfile.ZipFile("zips/ndc8.zip") as zfile:
    with zfile.open("ndc8.ttl") as readfile:
        ndc8_items = parse_ndc_ttl("ndc8", io.TextIOWrapper(readfile, "utf-8"))
        ndc8_items = add_relate_ndc(ndc8_items)

with zipfile.ZipFile("zips/ndc9.zip") as zfile:
    with zfile.open("ndc9.ttl") as readfile:
        ndc9_items = parse_ndc_ttl("ndc9", io.TextIOWrapper(readfile, "utf-8"))
        ndc9_items = add_relate_ndc(ndc9_items)

# with codecs.open("zips/ndc9.ttl", "r", "utf-8") as file:
#     ndc9_items = parse_ndc_ttl("ndc9", file)
#     ndc9_items = add_relate_ndc(ndc9_items)

@api.route("/")
def index(req, resp):
    resp.content = api.template("index.html")

@api.route("/ndc8")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc8_items[:1000], ensure_ascii=False)

@api.route("/ndc8_notations")
def index(req, resp):
    notations = []
    for item in ndc8_items:
        if 'notation' in item and len(item['notation'])==1:
            notations.append(item['notation'][0])
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(notations, ensure_ascii=False)


@api.route("/ndc9")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(ndc9_items[:1000], ensure_ascii=False)

@api.route("/ndc9_notations")
def index(req, resp):
    notations = []
    for item in ndc9_items:
        if 'notation' in item and len(item['notation'])==1:
            notations.append(item['notation'][0])
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(notations, ensure_ascii=False)

@api.route("/down_dict")
def index(req, resp):
    resp.headers = {"Content-Type": "application/json; charset=utf-8"}
    resp.content = json.dumps(down_dict, ensure_ascii=False)


if __name__ == "__main__":
    api.run()