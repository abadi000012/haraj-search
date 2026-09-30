---
name: haraj-ad-analytics
description: Check where a Haraj (haraj.com.sa) seller's ads rank in category feeds and keyword search, detect ads Haraj is hiding, and read their paid view-campaign stats (the "عرض إحصائيات الإعلان" screen). Use when the user asks about Haraj ad ranking, visibility, views, impressions, campaigns (حملات المشاهدات), or why an ad isn't showing.
---

# Haraj ad analytics

Haraj's website talks to a public GraphQL API at `https://graphql.haraj.com.sa/?queryName=<Name>`.
`scripts/haraj.py` holds compact versions of the site's own queries; `scripts/rank.py` uses them.

## 1. Rank check (anonymous, use a non-personal IP)

```bash
cd scripts && python3 rank.py "<authorUsername>" "keyword 1" "keyword 2"
```

For every ad of the seller and each of its categories (in the ad's city) it prints the actual feed
position, where the ad *should* be given that feed's sort order, whether refresh works in that
feed, and page 1-5 search positions per keyword. An ad that is "MISSING (should be ~#N)" in its
feeds and absent from searches matching its own title is hidden by Haraj. Takes a few minutes
(it sleeps between calls). A cloud container / VPN IP is fine: these queries take no user input.

## 2. Owner-only data (needs the owner's login)

All return 401 anonymously:
- `GetPostViewsCampaignsByPostId(postId)`: campaign bought/achieved views, impressions (الظهور),
  points, targeting, running/completed.
- `GetPostDisabledReasons(postId)` -> `{reasonBody reasonCode}`: why an ad is hidden. The site shows
  it to the owner as "عرضك غير مرئي للآخرين". Codes: `POST_NEEDS_TO_BE_UPDATED`,
  `MUST_BUY_POST_VIEWS_CAMPAIGN`, `AUTHOR_IDENTITY_MUST_BE_CHECKED`, `MUST_HAVE_REGA_POST_LICENSE`,
  `MUST_HAVE_TOURISM_RENTAL_LICENSE`, `AUCTION_SELLER_CONFIRMATION_REQUIRED`.
- The per-ad stats modal (عرض إحصائيات الإعلان): views, impressions (الظهور), contact clicks,
  calls, chats, comments, likes, shares. **Impressions = 0 means the ad is hidden.**

Read these on the ad page in the user's logged-in browser, or call `gql(..., token=...)` with their
access token. Never ask the user to paste their password or token into chat.

`doesPostMustBuyPostViewsCampaign(postId)` works anonymously.

Derived numbers: views/impressions = click-through rate; points/achieved views = cost per view.
One phone-call click counts as several views (`costOfOneCallClickInViews`).

## How Haraj actually ranks (verified 2026-09-30/10-01)

- **Category feeds** (`posts` / FetchAds) sort differently per category. Detect it; don't assume:
  - by **last update**, so refresh (تحديث) moves the ad to the top: e.g. خدمات الشراء من المواقع العالمية,
    كل الحراج by city.
  - by **original post date**, so refresh is ignored: e.g. خدمات تعقيب, مشاريع واستثمارات,
    مستلزمات رياضية, حراج السيارات. There an ad sinks for good; only search keeps it findable.
  - Clicks, likes and comments never change feed order. `upRank` on a post is the *seller's*
    rating count, not likes.
- **Top-level "خدمات" feed is paid-only**: every listed ad is `isPromoted`. An ad tagged only
  `خدمات` (no sub-category) is invisible when browsing.
- **Campaigns** (`promotedPosts`) are injected as a block at the top of the targeted tag+city
  feed until the bought views run out. They do not boost search.
- **Keyword search** (`search`): ads with all the query words in the **title** come first; when
  every result matches, fresher ads rank higher. Account age, ratings, Nafath and paid commission
  did not predict search position.
- **Hidden ads**: near-duplicate ads from one seller get hidden from both feeds and search. Haraj
  sends a `similar_ads` notice: "نرجو تحديث عرضك الموجود مسبقا بدلا من إضافة عرض جديد".
  Keep one ad per service.
- Official factors (site help text): freshness (تحديث العرض), completeness/description (جودة العرض),
  account ratings (تقييمات حسابك). Campaign button needs: correct category, a price, enough
  description, one store per business, under the promoted-ads cap.

## Gotchas

- Both feed and search pages are **1-based**; page 0 silently repeats page 1. `feed()` handles it.
- HTTP 388 = invalid GraphQL query (e.g. passing `beforeUpdateDate` to `search`), not a rate limit.
- Sleep ~1.5 s between calls; 429 means slow down.
- `authorUsername` is ignored when combined with `tag` in FetchAds, and is ignored by `search`.
- Descriptions pasted with HTML entities show up to buyers as literal `&amp;bull;`. Check
  `bodyTEXT` for `&amp;`.
