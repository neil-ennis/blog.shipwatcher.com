# The ShipWatcher Blog

This repository contains the public static snapshot of [blog.shipwatcher.com](https://blog.shipwatcher.com/). The editable WordPress source and database stay in the private local installation at `C:\Repos\neil\code\neilennis.com\blog.shipwatcher.com`. Cloudflare Workers Static Assets serves files from `site/`.

## Layout

- `site/` is the reviewed Staatic export and its required assets.
- `site/postmap.json`, `site/p/index.html`, and `site/_redirects` preserve the numeric `/p/<id>` destinations used by `nbe.me/s/<id>` shortlinks.
- `site/404.html` is the static not-found page.
- `scripts/prepare_export.py` applies repeatable fixes after copying a fresh full Staatic export.
- `wrangler.jsonc` configures the static asset directory and both approved live hostnames: `blog.shipwatcher.com` and `www.blog.shipwatcher.com`.

## Refreshing the site

1. Back up the private WordPress database and files, then complete a **full** Staatic publication to a temporary local filesystem directory. Confirm the publication status is `finished`.
2. Replace `site/` with the copied export, retaining `site/_redirects`.
3. Run `python scripts/prepare_export.py site PATH_TO_WORDPRESS_DATA` from this repository.
4. Review the changed public files. Check local links, images, numeric shortlinks, representative pages, and the 404 page before committing.
5. Push the approved snapshot to `main`. Cloudflare's Git integration deploys it; verify the temporary and live URLs after the deployment succeeds.

The `nbe.me/s/<id>` redirector sends visitors to the live domain's `/p/<id>` route. Keep all existing entries in `postmap.json` and check redirected page IDs when refreshing. Some page IDs deliberately lead to other websites.

Many article images still load from `cdn2.neilennis.com`, and some embeds load from Flickr or YouTube. Moving this HTML site does not migrate those external services. Older Flash media files remain in the snapshot, although modern browsers generally cannot play Flash.

Never commit the WordPress installation, database, backups, credentials, caches, or migration working files to this public repository.

## Initial export

The local full Staatic publication finished on 16 October 2026 with 536 resources (22,097,104 bytes) before preparation. The prepared copy has 569 files: 32 locally referenced font files and one sidebar portrait were added; an unneeded REST API inventory page and a rendered security-plugin probe were removed; a 404 page and redirect file were added. The link audit checked 15,160 internal references with no missing local targets. All 125 numeric postmap destinations were checked; 9 intentionally lead to external sites.
