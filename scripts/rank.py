"""Where do a seller's ads show up right now? Anonymous, so run it from a non-personal IP.

usage: python3 rank.py "<authorUsername>" ["keyword" ...]

For each ad and each of its categories (in the ad's city) it reports the actual feed position,
the position the ad *should* have given how that feed sorts, and flags ads that are missing
(hidden by Haraj). Feeds sort either by last update (refresh works) or by original post date
(refresh is ignored); the sort key is detected per feed.
"""
import sys, time
from haraj import gql, feed

FEED_PAGES = 12  # ~240 ads per feed


def sort_key(items):
    """'updateDate' if the feed is ordered by last refresh, else 'postDate'."""
    organic = [x for x in items if not x["isPromoted"]]

    def violations(k):
        v = [x[k] for x in organic]
        return sum(1 for a, b in zip(v, v[1:]) if a < b)

    return "updateDate" if violations("updateDate") < violations("postDate") else "postDate"


def feed_report(ad, tag):
    items = feed("FetchAds", {"tag": tag, "city": ad["city"], "limit": 20}, pages=FEED_PAGES)
    organic = [x for x in items if not x["isPromoted"]]
    if not organic:
        return f"{tag}: paid-only feed (only promoted ads are listed)"
    key = sort_key(items)
    ids = [x["id"] for x in items]
    found = ids.index(ad["id"]) + 1 if ad["id"] in ids else None
    expected = next((i + 1 for i, x in enumerate(items)
                     if not x["isPromoted"] and x[key] < ad[key]), None)
    how = "refresh works" if key == "updateDate" else "sorted by post date, refresh ignored"
    if found:
        state = f"#{found}"
    elif expected:
        state = f"MISSING (should be ~#{expected}) -> hidden"
    else:
        state = f"deeper than {len(items)} ads"
    return f"{tag}: {state} [{how}]"


def main(author, keywords):
    now = time.time()
    ads = feed("FetchAds", {"authorUsername": author, "limit": 50}, pages=2)
    print(f"{len(ads)} ads for {author}\n")
    print("CATEGORY FEEDS (in the ad's city):")
    for a in ads:
        promo = "PROMOTED " if a["isPromoted"] else ""
        print(f"- {a['id']} {promo}{a['city']} | posted {(now - a['postDate']) / 86400:.1f}d, "
              f"updated {(now - a['updateDate']) / 3600:.1f}h ago | {a['title'][:45]}")
        for tag in [t for t in a["tags"] if t != "كل الحراج"]:
            print("    " + feed_report(a, tag))
    if keywords:
        print("\nKEYWORD SEARCH (relevance order; first 5 pages):")
        mine = {a["id"] for a in ads}
        for kw in keywords:
            items = feed("Search", {"search": kw, "limit": 20}, pages=5)
            hits = [(i + 1, x["id"]) for i, x in enumerate(items) if x["id"] in mine]
            print(f"- {kw}: {hits or 'none of your ads in top %d' % len(items)}")
    print("\nAds missing from every feed AND every search above are almost certainly hidden: open them")
    print("while logged in and look for 'عرضك غير مرئي للآخرين', or check ظهور = 0 in عرض إحصائيات الإعلان.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
