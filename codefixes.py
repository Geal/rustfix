import re
from sets import Set

class CodeFix:
    def __init__(self, description, search, replace):
        self.description = description
        self.search      = search
        self.replace     = replace

fixes = []
fix   = CodeFix("attribute fix (cf mozilla/rust#2569)", r'(#\[)([^\]]*?)(\];)', r'#![\2]')
fix2  = CodeFix("priv attribute removal (cf mozilla/rust@f2a5c7a179ab0fc0e415918c1fc5d280a9e02ede)", r'(priv )', r'')
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
    else:
        return matchobj.group('crates') + matchobj.group("rest")

fix4 = CodeFix("crate extra was removed", r'(?P<crates>(?P<extern>extern crate .*?;\n)+)(?P<rest>.*)',crate_replace)

def import_crate_log(matchobj):
    if matchobj.group(0) == '':
        return ''
    crates = Set(matchobj.group('crates').split('\n'))
    if(len(crates) == 0):
        return ''

    macros = re.findall(r"(error\!|debug\!|info\!|log\!|log_enabled\!|warn\!)", matchobj.group("rest"))
    if (len(macros) > 0) and ("extern crate log;" not in crates):
        crates.add("extern crate log;")

        res = "#![feature(phase)]\n#[phase(syntax, link)]\nextern crate log;\n"
        res += matchobj.group('crates')
        #for el in crates:
        #    res += el+"\n"
        return res + matchobj.group("rest")
    else:
        return matchobj.group('crates') + matchobj.group("rest")

fix5 = CodeFix("logging macros need the log crate", r'(?P<crates>(?P<extern>extern crate .*?;\n)+)(?P<rest>.*)', import_crate_log)

fix6 = CodeFix("update the channel constructor (cf mozilla/rust@78580651131c9daacd7e5e4669af819cdd719f09)", r'Chan::new', r'comm::channel')
fix7 = CodeFix("Rename Chan to Sender (cf mozilla/rust@78580651131c9daacd7e5e4669af819cdd719f09)", r'Chan', r'Sender')
fix8 = CodeFix("Rename Port to Receiver (cf mozilla/rust@78580651131c9daacd7e5e4669af819cdd719f09)", r'Port', r'Receiver')
fix9 = CodeFix("New vec library (cf mozilla/rust#12771)", r'vec::(from_fn|from_raw_parts|from_slice|from_elem|from_iter|with_capacity)', r'Vec::\1')
fix10 = CodeFix("New vec library (cf mozilla/rust#12771)", r'use std::vec;', r'use std::vec::Vec;')

fixes.append(fix)
fixes.append(fix2)
fixes.append(fix3)
fixes.append(fix4)
fixes.append(fix5)
fixes.append(fix6)
fixes.append(fix7)
fixes.append(fix8)
fixes.append(fix9)
fixes.append(fix10)
