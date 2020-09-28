import glob, io, sys, json
from frontmatter import Frontmatter

def get_stream_or_stdout(fs):
    # for debugging, uncomment the next line
    # return sys.stdout
    return fs

class MDPost:
    def __init__(self, filename: str, attrs: dict):
        self.filename = filename
        self.attrs = attrs

class MDIndices:
    def __init__(self, cacheFileName):
        self.personIndex = {}
        self.tagIndex = {}
        self.postIndex = []
        self.actionItemProcessedPosts = set()

        try:
            with open(cacheFileName, mode="r") as f:
                data_list = json.load(f)
                self.actionItemProcessedPosts = set(data_list)
        except Exception as e:
            print(e)

    def saveCache(self, cacheFileName):
        with open(cacheFileName, "w") as f:
            setAsList = list(self.actionItemProcessedPosts)
            json.dump(setAsList, f)

    def addPost(self, post):
        self.postIndex.append(post)

        people = post.attrs['people']
        if people is None:
            return
        for p in people:
            self.addPerson(p, post)

        tags = post.attrs['tags']
        if tags is None:
            return
        for t in tags:
            self.addTag(t, post)


    def addPerson(self, person, post):
        self.addItemToIndex(person, self.personIndex, post)

    def addTag(self, tag, post):
        self.addItemToIndex(tag, self.tagIndex, post)

    def addItemToIndex(self, item, index, post):
        if item not in index:
            index[item] = []
        index[item].append(post)

    def makeStringList(self, strings):
        if type(strings) is str:
            return [strings]
        else:
            return strings

    def printStringsAsMarkdownList(self, filestream, key, values, oneLiner=False):

        fs = get_stream_or_stdout(filestream)
        if values is None:
            return

        valuesList = self.makeStringList(values)

        count = len(valuesList)
        if count == 0:
            return
        elif count == 1:
            fs.write(f' - {key}: {values}\n')
        elif oneLiner == False:
            fs.write(f' - {key}:\n')
            for v in values:
                fs.write(f'   - {v}\n')
        else:
            fs.write(f' - {key}: {", ".join(valuesList)}\n')

    def sortPostsByDate(self, post_list, olderFirst=False):
        post_sorted_list = sorted(post_list, key=lambda x: x.attrs["date"], reverse=(not olderFirst))
        return post_sorted_list

    def postProcessSummaries(self, filestream):
        fs = get_stream_or_stdout(filestream)

        fs.write(f'\n# Meeting summaries\n\n')

        post_sorted_list = self.sortPostsByDate(self.postIndex, olderFirst=False)
        for p in post_sorted_list:
            fs.write(f'\n## {p.attrs["name"]} @ {p.attrs["date"]}\n\n')
            for _, k in enumerate(p.attrs):
                if k not in [ "name", "date"]:
                    if k in [ "tags", "people"]:
                        short = True
                    else:
                        short = False
                    self.printStringsAsMarkdownList(fs, k, p.attrs[k], oneLiner=short)

                    # fs.write(f'{k}: {p.attrs[k]}\n')
                # fs.write(json.dumps(p.attrs[k], indent=1))
            # print(f'{p.attrs}\n')

    def postProcessActionItems(self, filestream):
        fs = get_stream_or_stdout(filestream)

        fs.write(f'\n# New followup items\n\n')

        post_sorted_list = self.sortPostsByDate(self.postIndex, olderFirst=True)
        for p in post_sorted_list:

            if p.filename in self.actionItemProcessedPosts:
                continue
            else:
                followups = p.attrs['followup']
                if type(followups) is str:
                    fs.write(f' - [ ] {followups}\n')
                else:
                    for f in followups:
                        fs.write(f' - [ ] {f}\n')

                self.actionItemProcessedPosts.add(p.filename)

        fs.write('\n\n')

    def postProcessIndex(self, filestream, index_name, index):
        fs = get_stream_or_stdout(filestream)

        fs.write (f'\n# {index_name} index\n\n')

        for k in index:
            fs.write(f'\n## {k}\n')

            sorted_posts = self.sortPostsByDate(index[k])
            for post in sorted_posts:
                fs.write (f' - {post.attrs["name"]} - {post.filename}\n')
    

cacheFileName = "./meetings_index/actionItemProcessedPosts.cache"

indices = MDIndices(cacheFileName)

for fname in glob.glob("meetings/**/*.md", recursive=True):

    # if fname.startswith("index\\"):
    #     continue

    # if fname.startswith("template\\"):
    #     continue

    print(f'Processing file: {fname}')
    post = Frontmatter.read_file(fname)
    attrs = post['attributes']
    if attrs is None:
        continue

    # for i, k in enumerate(attrs):
    #     print(f'{k}: {attrs[k]}')

    mdpost = MDPost(fname, attrs)
    indices.addPost(mdpost)

with open("./meetings_index/ix_people.md", "w") as f_people:
    indices.postProcessIndex(f_people, "People", indices.personIndex)

with open("./meetings_index/ix_tags.md", "w") as f_tags:
    indices.postProcessIndex(f_tags, "Tags", indices.tagIndex)

with open("./meetings_index/ix_summary.md", "w") as f_summary:
    indices.postProcessSummaries(f_summary)

with open("./tasks/meeting_tasks.md", "a") as f_tasks:
    indices.postProcessActionItems(f_tasks)

indices.saveCache(cacheFileName)
