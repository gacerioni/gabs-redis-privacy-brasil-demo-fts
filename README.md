# Privacy Brasil Demo: Redis Search with Synonyms, Fuzzy, Stemming, Phonetic, and Aliases

This project demonstrates how to use **Redis Stack** (with RediSearch)
to build a search demo for **Privacy Brasil**, showcasing advanced
search strategies for content creators, including:

-   **Synonyms** (single-token misspellings/variants)
-   **Aliases / multi-word synonyms** via a dedicated `aka` field (e.g.,
    *miss bumbum* → Andressa Urach)
-   **Fuzzy search** using Levenshtein distance (`%` for LD=1, `%%` for
    LD=2)
-   **Phonetic matching** (`PHONETIC dm:pt`) for Portuguese names
-   **Stemming** (`LANGUAGE portuguese`) for inflected terms in bios

## Requirements

-   Python 3.9+
-   [Redis Stack](https://redis.io/docs/latest/stack/) running locally

Install Python dependencies:

``` bash
pip install redis
```

Run Redis Stack with Docker:

``` bash
docker run -d -p 6379:6379 redis/redis:8
```

## How to Run

Clone this repo and run the demo script:

``` bash
python demo_privacy_brasil_search.py
```

## What It Does

The script will:

1.  Seed Redis with \~25 JSON documents of content creators (including
    **Andressa Urach**).
2.  Create a RediSearch index with:
    -   Portuguese stemming
    -   Phonetic matching on `name`
    -   `aka` alias field for multi-word nicknames
3.  Add a synonym group for **single-token variants** (e.g., *andresa*,
    *uraque*).
4.  Run example queries:

-   **Exact match:** `@name:"Andressa Urach"`\
-   **Alias field:** `@aka:"miss bumbum"` → finds Andressa\
-   **Fuzzy LD=1:** `@name:(%andresa%)`\
-   **Fuzzy LD=2:** `@name:(%%uratch%%)`\
-   **Phonetic:** `@name:(Andresa Oraki)` → matches Andressa\
-   **Stemming:** `@bio:(apresentações)` → matches bios with
    *apresentadora*, *apresentar*, etc.

## Expected Output

Example snippet from running the script:

    === Alias field (term 'miss bumbum') ===
    Total: 1
    - creator:andressa-urach | name=Andressa Urach | tags=brasil | customer=Privacy Brasil

## Notes

-   RediSearch **synonym groups** expand **single tokens only**. Use the
    `aka` field for multi-word aliases.
-   You can extend the dataset with more creators or more aliases
    easily.
-   Inspect synonym groups with:

``` bash
FT.SYNDUMP idx:creators
```

## License

MIT
