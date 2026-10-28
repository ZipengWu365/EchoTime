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
