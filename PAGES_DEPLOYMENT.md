# GitHub Pages-ready similarity demos

This repository now ships a GitHub Pages-ready static site bundle and workflow files. Deployment itself still happens in your GitHub repository, not inside the Python package.

- Push the repo with docs/ and .github/workflows/pages.yml included.
- Enable GitHub Pages in the repository settings or rely on the workflow to publish the docs bundle.
- Set the README live-demo link to the published Pages URL once the first deployment succeeds.
- Use docs/playground.html as the product demo landing page if you want a tighter viral loop than the full docs homepage.
- The published canonical base is https://zipengwu.me/EchoTime/; the github.io address redirects there. Update PROJECT_DOCUMENTATION_URL and package URLs together if the public domain changes.
- The Pages export adds unique descriptions, canonical URLs, social metadata, structured data, and sitemap.xml. New HTML pages need an intentional summary in src/echotime/seo.py.
- Submit https://zipengwu.me/EchoTime/sitemap.xml in an already verified Google Search Console property covering this URL. Publishing a sitemap does not guarantee indexing or rankings.
- robots.txt is controlled by https://zipengwu.me/robots.txt at the origin root; /EchoTime/robots.txt cannot set crawl policy. The project export intentionally does not create it.


## Automatic article publication

Add or edit a public Markdown article at `docs/articles/<filename>.md`, then
push it to `main`. The Pages workflow rebuilds the reading bundle before
installing/exporting EchoTime; no generated HTML needs to be committed for a
new article. The filename determines its stable address:
`https://zipengwu.me/EchoTime/articles/<filename>.html`.

Include one `#` heading and, optionally, simple metadata at the top:

```markdown
---
title: A descriptive article title
description: A short summary of what the reader will learn.
lang: en
---

# A descriptive article title

Article text.
```

Use `.en.md` or `.zh-CN.md` for language variants, or set `lang` explicitly.
`README.md`, `index.md`, dot/underscore files, draft/internal prefixes and
`.draft.` files are not published as articles. The article index, source
fingerprints, metadata and sitemap are built automatically. To keep an
existing address, retain its filename. Relative links to other public articles
are rewritten to their published pages; links to repository-only files stay
on GitHub. Local Markdown image links use the raw GitHub image URL.

The build also publishes `articles/catalog.json` with an `articles` array of
`path`, `title`, `language` and `description` records for the personal site's
combined index. `publication-source.json` records the deployed repository and
source revision, plus SHA-256 hashes of the exported article catalog and
sitemap. The combined publisher verifies these together before linking to newly
added articles, avoiding mixed versions during deployment or CDN propagation.
Failed builds leave the last deployed site available.
