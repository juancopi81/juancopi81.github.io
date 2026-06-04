# Juan Carlos Personal Site

Personal website for public projects, writing, and links.

Published with GitHub Pages from this repository.

## Structure

- `index.html` — homepage
- `projects.html` — selected personal/public projects
- `writing.html` — published writing
- `posts/` — individual static blog posts
- `templates/post-template.html` — copy/paste starter for new posts
- `about.html` — bio and links
- `styles.css` — shared styles

## Blog Workflow

Each blog entry is a standalone HTML file. There is no CMS, build step, or
database.

1. Copy `templates/post-template.html`.
2. Paste it into `posts/YYYY-MM-DD-short-title.html`.
3. Update the `<title>`, `<h1>`, date, tags, and body sections.
4. Add a card to the `Research Log` section in `writing.html`, newest first.
5. Preview locally before publishing.

Suggested first-principles shape:

- `The Question` — one precise thing you are trying to understand.
- `Why I Care` — why the point matters for intuition, implementation, or a
  project.
- `Setup and Definitions` — the primitives: variables, assumptions, notation,
  or toy example.
- `Minimal Derivation or Experiment` — only the smallest technical core needed
  to answer the question.
- `What I Think I Learned` — the current conclusion in plain language.
- `Open Questions` — what still feels unresolved.
- `References` — papers, docs, repos, or notebooks.

Math rendering:

- Use `\( ... \)` for inline math.
- Use `\[ ... \]` for displayed equations.
- The post template loads MathJax from a CDN, so equations render on GitHub
  Pages and during local preview when internet access is available.

Card snippet for `writing.html`:

```html
<article class="card post-card">
  <p class="eyebrow">Research Log</p>
  <h3><a href="posts/YYYY-MM-DD-short-title.html">Post title</a></h3>
  <p class="post-meta">Month D, YYYY · Topic · Tag</p>
  <p>
    One or two sentences summarizing the question and what the post tries to
    clarify.
  </p>
  <a href="posts/YYYY-MM-DD-short-title.html">Read note</a>
</article>
```

## Local Preview

Open `index.html` directly in a browser, or run:

```bash
python3 -m http.server 8765
```

Then visit `http://127.0.0.1:8765`.
