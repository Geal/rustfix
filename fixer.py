import os,sys,random,string
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

def clone(github_repo):
    print "cloning "+github_repo.username+"/"+github_repo.repository_name
    r = Repo.clone_from("https://github.com/"+github_repo.username+"/"+github_repo.repository_name, os.path.expanduser("./"+github_repo.repository_name))
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

def proceed(name, project):
    remote      = GithubRepo(name, project)
    forked_repo = fork(remote)
    forked      = GithubRepo("Geal", project)
    local       = clone(forked)
    head        = branch(local, "easyfix")
    return local

proceed("andelf", "rust-iconv")
