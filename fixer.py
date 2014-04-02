import os,sys,random,string,fnmatch,re
from sets import Set
import git
from git import Repo
from github import Github
from ConfigParser import SafeConfigParser

from codefixes import fixes

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
        test_remote = r.create_remote('geal',  "https://Geal:"+Config.getToken()+"@github.com/Geal/"+github_repo.repository_name)
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
    return branch_name


def githubrepo(repo):
    g = Github(Config.getToken())
    r = g.get_repo(repo.username+"/"+repo.repository_name)
    return r

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

def proceed(option, name, project):
    remote      = GithubRepo(name, project)
    forked_repo = fork(remote)
    forked      = GithubRepo(name, project)
    local       = clone(forked)
    head        = branch(local, "rustfix")
    files       = findFiles(os.path.expanduser("./"+remote.username+"-"+remote.repository_name), "*.rs")
    #print files

    res = Set([])
    for f in files:
        s = applyToFile(f, fixes)
        res.update(s)

    msg = "Automated fixes to follow Rust development\n\nApplied fixes:\n"
    for el in res:
        print "applied "+el
        msg += "\t*"+el+"\n"

    if option == "testfix":
        return

    index = local.index
    for (path, stage), entry in index.entries.iteritems():
        #print "adding "+path+" for stage: "+str(stage)
        index.add([path])

    new_commit = index.commit(msg)
    geal_origin = local.remotes.geal
    refspec = "refs/heads/"+head+":refs/heads/"+head
    geal_origin.push(refspec)

    if option == "commit":
        return

    title = "Automated fixes to follow Rust development"
    body  = """Hi,

This is an automated pull request to help you follow recent Rust developments.
Those changes were applied automatically to spare you the tedious search and replace work needed.

This is still in testing, and will not replace manual compilation (but will probably remove the annoying part). This may not compile out of the box, because that script does not analyze the type (yet)

If you do not want to receive those kinds of pull requests, I apologize forthis annoying notification and will not bother you again with this.
If you have ideas about how to improve that system, you can check it out at https://github.com/Geal/rustfix

You can reach me here on Github, or on IRC (Freenode, Mozilla, etc) by the nickname 'geal'.

Here are the fixes applied:

"""
    for el in res:
        body += "\t*"+el+"\n"

    body += "\nCheers!"

    print "creating a pull request with base: master and head: "+"Geal:"+head
    pull_request = githubrepo(remote).create_pull(title, body, "master", "Geal:"+head)
    print "pull request generated for "+name+"/"+project+" with id number "+str(pull_request.id)
    return local


if __name__ == "__main__":
    proceed(sys.argv[1], sys.argv[2], sys.argv[3])
