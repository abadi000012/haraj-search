"""Minimal anonymous client for Haraj's public GraphQL API (same queries the website uses)."""
import json, sys, time, urllib.request

URL = "https://graphql.haraj.com.sa/?queryName={name}&clientId=anon&version=N0.0.1"
FIELDS = "id title postDate updateDate authorUsername city tags isPromoted commentCount upRank downRank status URL"

Q = {
    # Category / city feed (what users see when browsing a tag)
    "FetchAds": """query FetchAds($id:[Int],$city:String,$authorUsername:String,$page:Int,$limit:Int,$tag:String,$beforeUpdateDate:Int){
      posts(id:$id,city:$city,authorUsername:$authorUsername,page:$page,limit:$limit,tag:$tag,beforeUpdateDate:$beforeUpdateDate){
        items{%s} pageInfo{hasNextPage}}}""" % FIELDS,
    # Keyword search
    "Search": """query Search($search:String!,$city:String,$tag:String,$page:Int,$limit:Int){
      search(search:$search,city:$city,tag:$tag,page:$page,limit:$limit){
        items{%s} pageInfo{hasNextPage}}}""" % FIELDS,
    # Paid campaign slots shown on top of a tag feed
    "PromotedPosts": """query PromotedPosts($tag:String!,$city:String){
      promotedPosts(tag:$tag,city:$city){items{%s}}}""" % FIELDS,
    # Campaign stats behind "عرض إحصائيات الإعلان" -- needs the owner's login token (401 anonymously)
    "GetPostViewsCampaignsByPostId": """query GetPostViewsCampaignsByPostId($postId:Int!){
      getPostViewsCampaignsByPostId(postId:$postId){items{
        id purchasePriceInCoins targetedCity isTargetingAllCities targetedTags totalPurchasedViews
        totalAchievedViews totalAchievedImpressions totalAdjustedAchievedViewsWithCallCost
        isRunning isCompleted}}}""",
}

def gql(name, variables, token=None):
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if token:
        headers["authorization"] = "Bearer " + token
    body = json.dumps({"query": Q[name], "variables": variables}).encode()
    req = urllib.request.Request(URL.format(name=name), data=body, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            if d.get("errors"):
                raise RuntimeError(d["errors"])
            return d["data"]
        except (OSError, RuntimeError) as e:
            code = getattr(e, "code", 0)
            # 388 = invalid query (e.g. an undeclared argument), 401 = needs login: retrying won't help
            if attempt == 2 or code in (388, 401):
                raise
            time.sleep(30 if code == 429 else 2 ** attempt)

def feed(name, variables, pages=3):
    """Walk pages the way the site does (page N + beforeUpdateDate of first item of previous page)."""
    key = {"FetchAds": "posts", "Search": "search"}[name]
    out, v = [], dict(variables, page=0)
    for p in range(pages):
        res = gql(name, v)[key]
        time.sleep(1.5)
        out += res["items"]
        if not res["pageInfo"]["hasNextPage"] or not res["items"]:
            break
        v = dict(variables, page=p + 1)
        if name == "FetchAds":  # feed pages are anchored on the previous page's first updateDate
            v["beforeUpdateDate"] = res["items"][0]["updateDate"]
    return out

if __name__ == "__main__":
    print(json.dumps(gql(sys.argv[1], json.loads(sys.argv[2])), ensure_ascii=False, indent=1))
