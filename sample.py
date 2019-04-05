import codecs
import io
import zipfile
import ndc_parser

with zipfile.ZipFile("zips/ndc8.zip") as zfile:
    with zfile.open("ndc8.ttl") as readfile:
        ndc8_items_source = ndc_parser.parse("8", io.TextIOWrapper(readfile, "utf-8"))
        ndc8_items = {}
        for key, item in ndc8_items_source.items():
            i = item.copy()
            del i["source"]
            ndc8_items[key] = i

print(ndc8_items)

with zipfile.ZipFile("zips/ndc9.zip") as zfile:
    with zfile.open("ndc9.ttl") as readfile:
        ndc9_items_source = ndc_parser.parse("9", io.TextIOWrapper(readfile, "utf-8"))
        ndc9_items = {}
        for key, item in ndc9_items_source.items():
            i = item.copy()
            del i["source"]
            ndc9_items[key] = i

print(ndc9_items)


# with codecs.open("zips/ndc9.ttl", "r", "utf-8") as file:
#     ndc9_items = ndc_parser.parse("ndc9", file)
#     ndc9_items_updown = add_relate_ndc(ndc9_items)
