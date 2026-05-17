# LEARN.md — asrock-geo-pipeline

> A plain-language deep-dive into what this project does, how it works, the decisions behind it, and the lessons learned along the way. Written for humans, not compilers.

---

## The Problem We Were Solving

Imagine you've spent years writing detailed product descriptions for 2,370 hardware products. They live in a database, they look great on the website, and your customers can read them just fine. Then a new wave of users arrives — not humans, but AI search engines like Google AI Overviews, Perplexity, and ChatGPT Search. These systems don't browse your website the way a person does. They scan structured signals. And your carefully crafted HTML briefs? To them, it's noise wrapped in tags.

**GEO (Generative Engine Optimization)** is the answer to this problem — the discipline of making your content legible to AI-driven search and summarization engines. The key currency is `Schema.org JSON-LD`: a structured data format that you embed invisibly in a webpage's `<head>`, speaking directly to search crawlers in a language they trust.

This project is a pipeline that transforms ASRock's raw product briefs into exactly that format — at scale, with AI, with a human review step baked in.

---

## Architecture at a Glance

The whole thing is three scripts chained together:

```
Excel (A: model, B: brief HTML)
        │
        ▼
[Step 1] generate_schema_description_llm.py
        │  Claude API rewrites each brief into a clean, GEO-optimized description
        │  Result written back to column C
        ▼
[Step 2] generate_jsonld.py
        │  Reads columns A + C, wraps each product in Schema.org JSON-LD format
        │  Outputs one .json file per product category
        ▼
[Step 3] build_preview.py
        │  Embeds all JSON-LD data into a single self-contained HTML file
        ▼
preview.html  ←  humans review this
*.json        ←  engineers embed these in <head>
*.xlsx        ←  returned to the web team (column C now populated)
```

Each script is independently runnable and stores results back to disk before the next step begins. This means if step 2 fails, you don't have to re-run the expensive LLM step — the Excel files already hold the results.

---

## The Three Scripts, Explained

### Script 1: `generate_schema_description_llm.py`

This is the engine of the pipeline. It takes raw HTML-contaminated product briefs and turns them into clean, natural-language descriptions that AI search engines can parse and cite.

**How it handles the data:**

The input briefs are messy. They contain:
- HTML tags like `<ul>`, `<li>`, `<strong>`
- Excel carriage-return artifacts that appear as the literal string `_x000D_`
- Multiple sentence fragments that don't form readable prose

The script strips all of that via Python's built-in `html.parser`, then ships the cleaned text to Claude in batches of 20 products per API call. Claude returns a JSON array of descriptions in the same order.

**Why batches of 20?**

It's a balance between API efficiency and reliability. Sending 2,370 individual requests would be slow and expensive. Sending one giant request would time out and make errors hard to recover from. A batch of 20 gives Claude enough context to produce consistent output while keeping individual requests small enough to be fast and retryable.

**The `cache_control` trick:**

Every API call uses the same system prompt — the detailed instructions about how descriptions should be written. By marking the system prompt with `"cache_control": {"type": "ephemeral"}`, we tell the Anthropic API to cache that prompt across calls. This means we only pay to process it once, even though it appears in every request. On a 119-batch run, this is a meaningful cost saving.

**Retry with exponential backoff:**

The script retries failed batches up to 3 times, with waits of 2s, 4s, and 8s. This is standard practice for any API-dependent code. APIs have transient failures — server overloads (we hit a 529 during the MB batch), occasional malformed responses, temporary network hiccups. Retrying quietly handles all of these without crashing the whole run.

**Fallback to rule-based output:**

If all retries fail for a batch, the script falls back to simply using the cleaned brief text directly. This ensures every row in the Excel still gets *something* written to column C — no product is left blank — even if the LLM was temporarily unavailable.

---

### Script 2: `generate_jsonld.py`

This script does one job cleanly: read columns A and C, wrap each row in a Schema.org `Product` object, and write a JSON file.

The output format is a JSON array (not a single object), which makes it easy to process programmatically — the web team can loop through the array and insert each item into the appropriate product page.

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "CL-650G",
  "description": "CL-650G. 80 PLUS® GOLD Certified ATX3.1 ready ...",
  "brand": {
    "@type": "Brand",
    "name": "ASRock"
  }
}
```

The `@context` and `@type` fields are what make this readable to search engines. Without them, it's just a JSON blob. With them, it's a semantic declaration that Google, Bing, and AI summarizers can parse with confidence.

---

### Script 3: `build_preview.py`

This script has a different job from the other two — it's not for machines, it's for people.

It bundles all 2,370 products into a single HTML file with embedded JavaScript. The data lives as a `const DATA = {...}` variable in a `<script>` tag, which means the file works offline, with no server, no dependencies, no installation. You just double-click it.

The UI features a sidebar for category switching, real-time search, paginated product cards, and a toggle to expand the raw JSON-LD for any product. There's also a one-click copy button so a web engineer can grab a product's JSON-LD and paste it directly into a page's `<head>`.

The design philosophy here is important: **this file is the human checkpoint in an otherwise automated pipeline**. A product manager can open it, search for a product they know well, and ask: "Does this description sound right? Are the specs accurate?" That's the gate that catches anything the LLM got wrong before it goes live.

---

## Lessons Learned

### 1. `_x000D_` — the ghost in the spreadsheet

When Excel files are saved with Windows-style line endings and then read by Python's openpyxl, carriage returns sometimes survive as the literal string `_x000D_` rather than as whitespace. If you don't strip these, your descriptions end up with random `_x000D_` artifacts mid-sentence.

**The fix:** `text.replace("_x000D_", " ")` before any other processing. Always check for these when ingesting Excel data.

### 2. The decimal point problem

The original rule-based script split text on periods to extract sentence fragments. This worked fine until it encountered specs like `15.5 Gbps` — and split them into `15` and `5 Gbps`. The spec was destroyed.

**The fix:** A negative lookbehind/lookahead regex: `(?<!\d)\.(?!\d)` — this matches a period only when it is *not* surrounded by digits on both sides. It's a compact way to say "split on sentence-ending periods, but leave decimal points alone."

This kind of edge case is why rule-based text processing is fragile. It works until it doesn't, and the failures are silent (no errors, just wrong data). LLM-based approaches handle this naturally because the model understands language structure rather than pattern-matching characters.

### 3. Never trust API reliability alone — always retry

During the MB batch (1,652 rows), we hit an `Error code: 529 - overloaded_error` partway through. Without retry logic, the script would have crashed at row ~1,600, requiring a manual restart and careful tracking of which rows had already been processed.

With exponential backoff, the script paused for 2 seconds and tried again. The retry succeeded, and the run completed without any data loss or manual intervention. On a long-running job, this is the difference between a smooth pipeline and an afternoon of frustration.

### 4. The `got 19 items, expected 20` problem

LLMs sometimes don't follow instructions perfectly. We asked Claude to return exactly 20 descriptions — occasionally it returned 19, merging two similar products into one response. The script catches this by comparing the length of the returned array against the input batch and retrying if they don't match.

This is a good general pattern: **always validate LLM output structure before trusting it**, especially when you're using the output as data (not prose).

### 5. Store secrets outside version control — and automate the loading

The API key lives in `env.local`, which is listed in `.gitignore`. This is standard security practice — keys should never appear in git history, even in private repositories.

What makes this project slightly more ergonomic is that the script *automatically loads* `env.local` at startup. The user doesn't need to remember to run `export ANTHROPIC_API_KEY=...` every time. The `load_env_local()` function reads the file on startup. Small detail, but it removes a friction point that causes mistakes.

### 6. Intermediate persistence is free insurance

Each script writes its results to disk before the next script runs. The LLM results go into Excel column C; the JSON-LD results go into `.json` files. This means:

- You can re-run step 2 without re-paying for step 1
- You can inspect the data between steps
- A failure in step 3 doesn't lose step 2's work

This is the **checkpoint pattern** — break a long process into stages, persist the result of each stage, and make each stage independently restartable.

---

## Why LLM Over Rules?

The original approach was rule-based: strip HTML, clean whitespace, concatenate fragments up to 500 characters. It worked, but the output read like a robot assembling a sentence from spare parts:

> `CL-650G. 80 PLUS® GOLD Certified ATX3.1 Ready 120mm Golf-blade Fan Auto iCool Intelligent Fan Control Built-in 5V BOOST function Reliable 5-Year Warranty.`

Compare that to the LLM output:

> `CL-650G. 80 PLUS GOLD Certified ATX3.1 ready power supply with 120mm golf-blade fan, Auto iCool intelligent fan control, built-in 5V BOOST function, and reliable 5-year warranty.`

The second version reads like a sentence a person would write. It's the version an AI search engine is more likely to quote, because it sounds authoritative rather than assembled. The difference is narrative coherence — something rules can't produce but a language model does naturally.

The cost for the entire 2,370-product run was under $4 USD. For the quality improvement, that's an easy trade.

---

## The Stakeholder Design: Why `preview.html` Matters

There's a pattern in AI-assisted workflows that's easy to skip but important to keep: **AI generates, human reviews, then deliver**. Skipping the middle step is tempting when the AI output looks good — but it's how errors reach production undetected.

`preview.html` is the institutionalization of that middle step. It's not a debugging tool — it's a governance interface. A product manager who knows nothing about Schema.org can open it, find their product line, and read the descriptions. If a spec is wrong or a product is miscategorized, they'll catch it here.

This is what makes the pipeline trustworthy to non-technical stakeholders. The AI did the heavy lifting; the human had the final say. That accountability loop — visible, accessible, low-friction — is what earns buy-in for AI-augmented workflows inside organizations.

---

## Technology Choices, Justified

| Technology | Why |
|---|---|
| Python | Cross-platform, available everywhere, excellent library support for Excel and HTTP |
| `openpyxl` | The standard library for reading/writing `.xlsx` files without Excel installed |
| `anthropic` SDK | Official SDK for Claude API; handles auth, retries at transport layer, streaming |
| `claude-haiku-4-5` | Fastest and cheapest Claude model; sufficient for structured text transformation tasks |
| JSON-LD in `<script>` | Google's recommended format for structured data; doesn't interfere with page HTML |
| Self-contained HTML | No server dependency; anyone can open it on any machine, on or offline |

---

## What a Senior Engineer Would Notice

A few patterns in this codebase worth internalizing:

**Separation of concerns.** Each script does exactly one thing. The LLM script doesn't know about JSON-LD. The JSON-LD script doesn't know about HTML. The preview script doesn't know about Excel. This makes each one testable, replaceable, and debuggable in isolation.

**Fail loudly at startup, fail softly at runtime.** The LLM script checks for the API key immediately and raises a clear error if it's missing — before any work begins. But once the run starts, individual batch failures are retried quietly and logged, not crashed. This matches where human attention is most useful: setup errors need immediate intervention; transient API errors do not.

**The fallback is data, not silence.** When the LLM fails permanently, the script writes the cleaned brief text as the description. The column is never left empty. Downstream scripts (step 2, step 3) always have something to work with. Empty data is often harder to detect than imperfect data.

**Prompt as specification.** The system prompt in the LLM script is the canonical specification for what a "good description" looks like. It covers format, length, tone, prohibited content, and required content. Treating the prompt as the spec — not just casual instructions — is what makes LLM output consistent and auditable.

---

## Future Pitfalls to Watch

- **Excel file encoding**: `openpyxl` handles UTF-8 well, but if source Excel files are saved in legacy encodings (e.g., CP950 on Windows), you may see garbled output in terminal logs. The *data in the files* is usually fine; it's just console display that looks wrong. Always verify the actual Excel cell values, not just terminal output.

- **LLM output drift**: Language models are updated over time. A description that looks great today might sound slightly different if you re-run the pipeline in six months with a newer model version. If consistency across runs matters, pin the model version string explicitly.

- **Batch size and context limits**: A batch of 20 short PSU briefs is very different in token count from a batch of 20 long motherboard briefs. If you encounter `max_tokens exceeded` errors, reduce `BATCH_SIZE` for the affected file.

- **The `env.local` habit**: It's easy for a new team member to accidentally commit `env.local` before the `.gitignore` is set up. Verify `.gitignore` is in place before running `git add .` on a fresh clone.

---

## The Bigger Picture

This project is a small example of a pattern that will appear everywhere in the next few years: **humans have data, AI can reformat it at scale, and the combination creates value that neither could produce alone**.

The web team had 2,370 product descriptions that were perfectly readable to humans but invisible to AI search engines. Ten minutes of Python scripting and a few dollars of API calls changed that. The output isn't replacing anyone's job — the web team still manages their CMS, the PMs still approve the content, the engineers still embed the JSON-LD. The pipeline just removed a tedious manual conversion step that would have taken weeks to do by hand.

That's what good AI-augmented tooling looks like: it fits into existing workflows, it's auditable at every step, and the humans remain in control of what ships.
