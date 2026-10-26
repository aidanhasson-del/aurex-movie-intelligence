# Final GitHub checklist

- [ ] Confirm the **public copy** contains no `.venv`, `.env`, `.db`, ratings CSVs other than fictional example, `.joblib`, or AUREX/VERA private source.
- [ ] Confirm code review and choose a license if you want to grant reuse rights.
- [ ] Verify your own TMDB token works in a fresh `.env` (never commit it).
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Add enough of **your own** private ratings locally to train, then test training and a recommendation; do not upload the resulting DB or model.
- [ ] Review `git diff --cached --name-only` carefully before first commit.

```powershell
git init
git add .
git diff --cached --name-only
git commit -m "Publish AUREX Movie Intelligence"
git branch -M main
# Create an empty GitHub repository, then:
git remote add origin https://github.com/YOUR_USERNAME/aurex-movie-intelligence.git
git push -u origin main
```

The source archive originally uploaded included a complete ~321 MB Windows `.venv`, a SQLite DB, ratings CSVs and trained model artifacts. **Do not upload that original archive to GitHub.** This package intentionally strips them.
