from tinydb import TinyDB, Query

# we have a cap of 10 queries/s, thus we get a bunch of time to carefully analyze each one
# must-haves: live user prompt interaction+injection, dispatching summarizations, link crawling, link caching
# current goal: just scrape urls recursively (unwrapped, no actual recursion)

# todo: we will split crawler into 2 runtimes, one for crawling, one for embedding.
#       the embedding one will look through db_url for any not vectorized articles.
#       this will allow for automatic re-vectorization in case we get a new embed model.

db_url_path = 'store/data/urls.json'
db_url = TinyDB(db_url_path)

# 100 links max, then put new ones in db
# this ensures generally broad search
url_memory_limit = 100
url_memory = []

# url order:
# 0. use short memory urls
# 1. refill with non-researched db urls
# 2. refill with google search


def is_url_present(url: str):
    # 0. check short term mem for presence
    # 1. check db_url for presence
    pass


def schedule_url(url: str):
    # 0. check if url was already saved
    # 1. place in short-term memory
    # 2. otherwise add to the db
    pass


def process_url():
    # 0. download article
    # 1. extract all links
    # 1.0. fill up short-term mem
    # 1.1. fill up db_url
    # 2. update own db record with data
    # 2.0. uuid (key), url (old), date, file_hash, [embedded_by, ...]
    pass