# Translating the Wavu guide

Thank you for helping! This file is for translators and is not part of the
website (it is listed in `exclude_docs` in `mkdocs.yml`).

## How translations are stored

The site uses [mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/)
with the **suffix** layout. English is the default and has no suffix; a
translation sits **next to** the English page with the language code before
`.md`:

| Language | Code | Example file |
|---|---|---|
| English (default) | — | `start/install.md` |
| Français | `fr` | `start/install.fr.md` |
| Deutsch | `de` | `start/install.de.md` |
| Español | `es` | `start/install.es.md` |
| Русский | `ru` | `start/install.ru.md` |
| 日本語 | `ja` | `start/install.ja.md` |
| 한국어 | `ko` | `start/install.ko.md` |
| 繁體中文 | `zh-Hant` | `start/install.zh-Hant.md` |
| 简体中文 | `zh-Hans` | `start/install.zh-Hans.md` |

Untranslated pages fall back to English automatically, so you can translate
one page at a time. Preview with `pixi run -e docs docs-serve` and pick your
language in the header; check with `pixi run -e docs docs-build` (strict, must
pass) before opening a pull request.

Menu titles in the navigation come from each page's first `# Heading`. Section
names (*Start here*, *Write a script*, *Share*, *Help*) can be translated with
`nav_translations` under your language in `mkdocs.yml`.

## Rules

1. **Keep filenames and links unchanged.** Link to `install.md`, not
   `install.fr.md`; the plugin picks the right language.
2. **Never translate code**: code blocks, `PARAMS` keys and types
   (`"sigma"`, `"float"`), function names (`run`, `ctx.log`), file names
   (`script.py`, `pixi.toml`), commands (`pixi run test`) and Log messages
   that the reader must recognise.
   Comments inside code blocks may be translated.
3. **Menu paths and dialog texts stay in English, exactly as Fiji shows
   them**, because Fiji's menus are English. Add a translated gloss in
   parentheses if it helps, e.g.
   **Plugins › Wavu › Run Python Script** (Python-Skript ausführen).
   The same applies to button and field names (**OK**, **Sigma (pixels)**,
   **Debug in VS Code**).
4. **Keep image paths unchanged** (`../assets/img/restaurant.svg`).
   The illustrations are shared by all languages; translate only the
   alt text in `![…]`.
5. **Keep admonitions, tabs and buttons** (`!!! tip`, `=== "Windows"`,
   `{ .md-button }`) as they are; translate only their visible titles/text.
   Content-tab titles *Windows / macOS / Linux* stay in English.
6. **Keep the tone**: plain words, short sentences, the restaurant analogy
   first (Fiji = waiter, worker = kitchen, script = recipe, images =
   ingredients, environment = the recipe's own kitchenware, `pixi.toml` =
   kitchenware list, `pixi.lock` = receipt, container = the whole kitchen
   packed up with its kitchenware), then the steps, then the *In one sentence* recap.
   Explain any technical word the first time it appears. Use the informal
   "you" where your language allows it for friendly technical writing.
7. **Keep pages short**: a page must be readable in under five minutes,
   about 300–700 words, at most ~900 words excluding code (for Chinese,
   Japanese and Korean, roughly the same reading time). Do not add new
   material; if something is missing, open an issue for the English page.
8. **Mermaid diagrams**: you may translate the text inside the boxes; keep
   the node IDs, arrows and `classDef` lines unchanged.
9. If the English page changes, the translation should be updated in the
   same or a follow-up pull request. Mention the English commit you
   translated from in the pull request description.
