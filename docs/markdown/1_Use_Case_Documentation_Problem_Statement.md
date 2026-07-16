**USE CASE DOCUMENTATION**

**Enhancing Product Search with Large Language Models (LLMs)**

*Scope: Problem Statement Only*


# **1. Background**

Retail and e-commerce organizations depend on product search as the primary interface between a customer's intent and the products in a catalog. Search is one of the highest-leverage touchpoints in the online shopping journey: industry research consistently shows that customers who use site search convert at meaningfully higher rates than those who browse, but only when the search results they receive are actually relevant to what they typed.

Most production search stacks in retail today are still built primarily around keyword / lexical matching (inverted indexes, TF-IDF, BM25) layered with manual rules, synonym lists, and merchandising overrides. This approach was designed for a world where users type precise product names or SKUs, and it works reasonably well for that narrow case. It breaks down as soon as the customer's query and the product catalog's vocabulary diverge, which happens constantly in real catalogs of tens of thousands to millions of SKUs.

# **2. Problem Statement**

When customers search a retailer's site and cannot easily find what they are looking for, they become frustrated and are more likely to abandon the session, abandon the cart, or switch to a competitor's site entirely — directly translating lost search intent into lost revenue. This gap between customer intent and matched product is the core problem this use case addresses.

## **2.1 Why keyword-based search fails customers**

Vocabulary mismatch: a shopper searches “cozy reading chair” but the product is titled “accent armchair, upholstered” — no keyword overlap exists even though the product is exactly what the customer wants.

No understanding of synonyms or conceptual closeness: keyword engines do not natively know that “kid,” “child,” and “kids’” refer to the same audience, or that “sofa” and “couch” are interchangeable.

Users must guess the retailer's internal vocabulary: shoppers are forced to use precise catalog terminology instead of natural, descriptive language, shifting cognitive burden onto the customer.

Zero-result and low-relevance searches: ambiguous or descriptive queries (“something for a small apartment balcony”) frequently return no results or irrelevant results, ending the session.

Long-tail and voice/conversational queries are poorly served: as more search traffic shifts to longer, natural-language, and voice-driven queries, rigid keyword matching increasingly fails to interpret intent.

Manual curation does not scale: merchandising teams manually patch synonym dictionaries and boost/bury rules per query, which is labor-intensive, slow to update, and cannot keep pace with catalogs that add or change thousands of SKUs regularly.

## **2.2 Business impact of the problem**

Lost revenue: every failed or low-relevance search represents a purchase-intent signal that goes unconverted.

Increased bounce and cart abandonment: frustrated searchers leave the site rather than continuing to refine queries manually.

Erosion of customer trust and loyalty: repeated poor search experiences push customers toward competitors (including large marketplaces) known for stronger discovery experiences.

Higher cost-to-serve: reliance on manual merchandising rules and synonym curation consumes ongoing analyst and engineering time without ever fully closing the relevance gap.

Missed opportunity to differentiate: as more of retail commerce moves online, a superior search/discovery experience is one of the few remaining levers retailers control directly to compete with larger platforms.

## **2.3 Scale of the problem**

The scale of this problem grows with catalog size and traffic. As illustration, the Wayfair Annotation Dataset (WANDS) — used as the reference dataset for this use case — contains over 42,000 furniture and home-goods products, 480 real customer queries, and more than 233,000 human-labeled query-product relevance judgments. Even within this single category (furniture/home goods) and a modest query sample, the volume of query-product combinations that must be evaluated for relevance is enormous — and real retail catalogs and query volumes are typically orders of magnitude larger, and continuously changing.

## **2.4 Problem statement summary**


| Dimension | Current State (Pain) | Desired Outcome |
| --- | --- | --- |
| Query Understanding | Exact keyword match only; no concept of synonyms or intent | Understand natural, descriptive, conversational queries |
| Result Relevance | High rate of zero/low-relevance results on long-tail queries | Consistently relevant top-N results regardless of phrasing |
| Catalog Scale | Manual synonym/rule curation cannot keep up with 10K–1M+ SKUs | Automated, self-updating relevance that scales with catalog |
| Customer Behavior | Frustration, abandonment, switching to competitors | Higher conversion, satisfaction, and repeat engagement |
| Cost of Ownership | Ongoing manual merchandising/rule-tuning overhead | Lower operational overhead via a learned, adaptive model |


# **3. Statement in One Sentence**

*  Retailers need a way to understand the conceptual intent behind a customer's free-form search query — not just its literal keywords — and reliably match that intent to the most relevant products in a large, constantly evolving catalog, in order to reduce failed searches, cart abandonment, and lost revenue.*
