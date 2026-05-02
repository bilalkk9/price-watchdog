# Security Rules (enforce on every file)

1. **Secrets** — only from `config.py` / `.env`; never in logs, exceptions, or responses
2. **SQL** — parameterized queries only (`?` placeholders); no f-string SQL ever
3. **Input validation** — validate URLs, prices, and all user input at the boundary (not deep inside)
4. **HTTP headers** — realistic User-Agent; never send API keys in query params
5. **Error messages** — log full detail internally; surface only safe summary to user/dashboard
6. **Email** — App Password only (never real Gmail password); TLS required
7. **File paths** — use `pathlib.Path`; reject any path with `..` traversal
8. **Subprocess** — do not use; no shell=True ever
9. **Deps** — pin versions in requirements.txt; no wildcard `*` versions
10. **Rate limits** — respect Gemini free tier; 2s delay between API calls; exponential backoff on 429
