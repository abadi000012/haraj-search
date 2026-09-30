"""Where do a seller's ads show up right now? Anonymous, so run it from a non-personal IP.

usage: python3 rank.py "<authorUsername>" ["keyword" ...]
"""
import sys, time
from haraj import gql, feed

def main(author, keywords):
    now = time.time()
    ads = feed("FetchAds", {"authorUsername": author, "limit": 50}, pages=2)
    print(f"{len(ads)} ads for {author}\n")
    print("CATEGORY FEEDS (sorted by last update; position within ~100 newest):")
    for a in ads:
        age = (now - a["updateDate"]) / 3600
        spots = []
        for tag in [t for t in a["tags"] if t != "كل الحراج"]:
            items = feed("FetchAds", {"tag": tag, "city": a["city"], "limit": 20}, pages=5)
            pos = next((i + 1 for i, x in enumerate(items) if x["id"] == a["id"]), None)
            spots.append(f"{tag}/{a['city']}: {pos or 'not in top ' + str(len(items))}")
        promo = "PROMOTED " if a["isPromoted"] else ""
        print(f"- {a['id']} {promo}updated {age:.1f}h ago | {a['title'][:45]}\n    " + " | ".join(spots))
    if keywords:
        print("\nKEYWORD SEARCH (relevance order; first page only):")
        mine = {a["id"] for a in ads}
        for kw in keywords:
            items = gql("Search", {"search": kw, "limit": 20})["search"]["items"]
            hits = [(i + 1, x["id"]) for i, x in enumerate(items) if x["id"] in mine]
            print(f"- {kw}: {hits or 'none of your ads on page 1'}")
            time.sleep(1.5)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
