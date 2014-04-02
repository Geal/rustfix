import os,sys,random,string,fnmatch,re
from sets import Set
import git
from git import Repo
from github import Github
from ConfigParser import SafeConfigParser

class Config:
    current_path = path = os.path.abspath(os.path.dirname(sys.argv[0]))
    parser = SafeConfigParser()

    @classmethod
    def getToken(cls):
        cls.parser.read(cls.current_path+"/settings.ini")
        section = "credentials"
        return cls.parser.get(section, "github_token")

class GithubRepo:
    def __init__(self, username, repository_name):
        self.username        = username
        self.repository_name = repository_name

class CodeFix:
    def __init__(self, description, search, replace):
        self.description = description
        self.search      = search
        self.replace     = replace

def clone(github_repo):
    try:
        print "cloning "+github_repo.username+"/"+github_repo.repository_name
        r = Repo.clone_from("https://github.com/"+github_repo.username+"/"+github_repo.repository_name, os.path.expanduser("./"+github_repo.username+"-"+github_repo.repository_name))
        # FIXME add the token here
        test_remote = r.create_remote('geal',  "https://github.com/Geal/"+github_repo.repository_name)
        print "done"
        return r
    except git.exc.GitCommandError:
        print "already locally cloned, pulling recent changes"
        r = Repo(os.path.expanduser("./"+github_repo.username+"-"+github_repo.repository_name))
        r.heads.master.checkout()
        origin = r.remotes.origin
        origin.pull()
        print "done"
        return r

def branch(repo, fixname):
    rnd = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(5)])
    branch_name = fixname+"-"+rnd
    print "creating branch "+branch_name
    new_branch = repo.create_head(branch_name)
    print "checkout to "+new_branch.name
    new_branch.checkout()
    print "done"


def fork(github_repo):
    g = Github(Config.getToken())
##for repo in g.get_user().get_repos():
##    print repo.name

    r = g.get_repo(github_repo.username+"/"+github_repo.repository_name)
    print "forking "+r.full_name
    print "from url: "+r.clone_url
    u = g.get_user()
    forked = u.create_fork(r)
    return forked

#print "deleting "+r2.full_name
#r2.delete()

def findFiles(folder, pattern):
    print "looking for "+pattern+" in "+folder
    matches = []
    for root, dirnames, filenames in os.walk(folder):
      for filename in fnmatch.filter(filenames, pattern):
          matches.append(os.path.join(root, filename))
    return matches

def applyToFile(filename, fixes_array):
    res = Set([])
    with open(filename,'r+') as f:
        text = f.read()
        for fix in fixes_array:
            print filename+":\tapplying '"+fix.description+"'"
            #print " -> "+str(re.subn(fix.search, fix.replace, text, flags = re.DOTALL | re.MULTILINE))
            text2 = re.sub(fix.search, fix.replace, text, flags = re.DOTALL | re.MULTILINE)
            if text != text2:
                res.add(fix.description)
                text = text2
                f.seek(0)
                f.write(text)
                f.truncate()

    return res

def proceed(name, project):
    remote      = GithubRepo(name, project)
    forked_repo = fork(remote)
    forked      = GithubRepo(name, project)
    local       = clone(forked)
    head        = branch(local, "easyfix")
    files       = findFiles(os.path.expanduser("./"+remote.username+"-"+remote.repository_name), "*.rs")
    #print files
    arr         = []
    fix         = CodeFix("attribute fix", r'(#\[)(.*)(\];)', r'#![\2]')
    fix2        = CodeFix("priv attribute removal", r'(priv )', r'')
    fix3        = CodeFix("extern mod is obsolete", r'extern mod', r'extern crate')
    def crate_replace(matchobj):
        if matchobj.group(0) == '':
            return ''
        crates = Set(matchobj.group('crates').split('\n'))
        if(len(crates) == 0):
            return ''
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
    arr.append(fix)
    arr.append(fix2)
    arr.append(fix3)
    arr.append(fix4)
    res = Set([])
    for f in files:
        s = applyToFile(f, arr)
        res.update(s)

    msg = "Automated fixes to follow Rust development\n\nApplied fixes:\n"
    for el in res:
        msg += "\t*"+el+"\n"

    index = local.index
    for (path, stage), entry in index.entries.iteritems():
        #print "adding "+path+" for stage: "+str(stage)
        index.add([path])

    new_commit = index.commit(msg)

    return local

proceed("divarvel", "rusty-spoon")
