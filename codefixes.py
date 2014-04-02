import re
from sets import Set

class CodeFix:
    def __init__(self, description, search, replace):
        self.description = description
        self.search      = search
        self.replace     = replace

fixes = []
fix   = CodeFix("attribute fix", r'(#\[)([^\]]*?)(\];)', r'#![\2]')
fix2  = CodeFix("priv attribute removal", r'(priv )', r'')
fix3  = CodeFix("extern mod is obsolete", r'extern mod', r'extern crate')

def crate_replace(matchobj):
    if matchobj.group(0) == '':
        return ''
    crates = Set(matchobj.group('crates').split('\n'))
    if(len(crates) == 0):
        return ''

    if "extern crate extra;" in crates:
        crates.remove("extern crate extra;")

    other_crates = re.findall(r"extra::(.*?)(::|;)", matchobj.group("rest"))
    for cr in other_crates:
        crates.add("extern crate "+cr[0]+";")

    rest = re.sub(r"extra::", r"", matchobj.group("rest"), flags = re.DOTALL | re.MULTILINE)
    res = ""
    for el in crates:
        res += el+"\n"
    return res + rest

fix4        = CodeFix("crate extra was removed", r'(?P<crates>(?P<extern>extern crate .*?;\n)+)(?P<rest>.*)',crate_replace)

fixes.append(fix)
fixes.append(fix2)
fixes.append(fix3)
fixes.append(fix4)
