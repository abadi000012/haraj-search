---
name: haraj-ad-analytics
description: Check where a Haraj (haraj.com.sa) seller's ads rank in category feeds and keyword search, and read their paid view-campaign stats (the "عرض إحصائيات الإعلان" screen). Use when the user asks about Haraj ad ranking, visibility, views, impressions, campaigns (حملات المشاهدات), or why an ad isn't showing.
---

# Haraj ad analytics

Haraj's website talks to a public GraphQL API at `https://graphql.haraj.com.sa/?queryName=<Name>`.
`scripts/haraj.py` holds compact versions of the site's own queries; `scripts/rank.py` uses them.

## 1. Rank check (anonymous, use a non-personal IP)

```bash
python3 scripts/rank.py "<authorUsername>" "keyword 1" "keyword 2"
```

Prints, for every ad of the seller: position in each of its category+city feeds, whether it is
promoted, hours since last update, and its page-1 position for each keyword search.
A cloud container / VPN IP is fine: these queries take no user or location input.

## 2. Campaign stats (needs the owner's login)

`GetPostViewsCampaignsByPostId` returns what "عرض إحصائيات الإعلان" shows: purchased vs achieved
views, impressions (الظهور), points spent, targeted city/tags, running/completed. Anonymously it
returns 401, so either:
- read it on the ad page in the user's logged-in browser (عرض إحصائيات الإعلان button), or
- call `gql("GetPostViewsCampaignsByPostId", {"postId": ID}, token=...)` with the user's access
  token. Never ask the user to paste their token into chat; read it only from their own browser
  session if they have given you access to it.

Useful derived numbers: views/impressions = click-through rate; points/achieved views = cost per view.
One phone-call click counts as several views (`costOfOneCallClickInViews`), so achieved views can
exceed purchased.

## How Haraj actually ranks (verified 2026-09-30)

- **Category feeds** (`posts` / FetchAds): strictly newest `updateDate` first. Paging uses
  `beforeUpdateDate`. Clicks, likes (upRank) and comments do not change the order. Paid campaign
  ads (`promotedPosts`) are injected as a block for the targeted tag+city.
- **Main "خدمات" feed**: in samples of 100+ ads, every item was `isPromoted=true`; unpaid service ads
  only show in sub-category feeds and search.
- **Keyword search** (`search`): text relevance, not freshness. Ads with all query words in the
  **title** fill page 1; body text and freshness only matter when few titles match. Campaigns do
  not boost search. Only ~20 results are shown (later pages repeat page 1).
- **Near-duplicate ads** from one seller tend to be missing from search: keep one ad per service
  and refresh it (Haraj's own guidance: "يرجى الاكتفاء بعرض واحد لكل سلعة ويمكنك تحديثه").
- Official factors (from the site's own help text): freshness (تحديث العرض), ad completeness/description
  (جودة العرض), and account ratings (تقييمات حسابك).

## Gotchas

- HTTP 388 = the GraphQL query is invalid (e.g. passing `beforeUpdateDate` to `search`). Not a rate limit.
- Sleep ~1.5 s between calls; 429 means slow down.
- Look up by `authorUsername` rather than a list of ids; multi-id lookups can drop items.
