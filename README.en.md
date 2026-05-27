# TE to Kindle

[![TE to Kindle](https://github.com/lkcp/te-to-kindle/actions/workflows/te-to-kindle.yml/badge.svg)](https://github.com/lkcp/te-to-kindle/actions/workflows/te-to-kindle.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
English | [简体中文](./README.md)

Automatically push the latest issue of *The Economist* from [evanbio/The_Economist](https://github.com/evanbio/The_Economist) to your Kindle every Sunday morning. Powered by GitHub Actions — no server, completely free.

## Features

- ⏰ **Scheduled delivery** — runs every Sunday at 09:10 Beijing time (01:10 UTC)
- 📚 **Multi-format** — mobi / epub / azw3 / pdf (selectable on manual trigger)
- 🔁 **Auto retry** — if the upstream is late, retries every 10 min up to 6 times
- 🪪 **Idempotent** — `last_sent.txt` tracks the last delivered issue to avoid duplicates
- 🔒 **Secret-safe** — all credentials live in GitHub Secrets, nothing hardcoded

## Quick Start

### 1. Fork or clone this repo

```bash
gh repo create te-to-kindle --private --clone
# copy the files from this repo and push
```

### 2. Get your Kindle delivery address

1. Sign in to [Amazon — Manage Your Content and Devices](https://www.amazon.com/hz/mycd) (or `.cn` / `.co.uk` etc.)
2. **Devices → your Kindle** — note the send-to-Kindle email (e.g. `xxx@kindle.com`)
3. **Preferences → Personal Document Settings → Approved Personal Document E-mail List** — add your sender address (e.g. `you@gmail.com`)

> ⚠️ Attachments from non-approved senders are silently dropped by Amazon.

### 3. Prepare an SMTP sender

Gmail example:

1. Enable 2-Step Verification
2. Create an [App Password](https://myaccount.google.com/apppasswords) (16 chars)
3. SMTP: `smtp.gmail.com:587`

QQ / 163 / Outlook also work — just plug their SMTP host and auth code into Secrets.

### 4. Configure GitHub Secrets

Repo **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Required | Example | Description |
|---|:-:|---|---|
| `KINDLE_EMAIL` | ✅ | `you_abc@kindle.com` | Your Kindle delivery email |
| `SMTP_USER` | ✅ | `you@gmail.com` | Sender (must be in Amazon's approved list) |
| `SMTP_PASS` | ✅ | `abcd efgh ijkl mnop` | SMTP auth code (NOT your login password) |
| `SMTP_HOST` | ⬜ | `smtp.gmail.com` | Defaults to Gmail |
| `SMTP_PORT` | ⬜ | `587` | Defaults to 587 |

### 5. Try a manual run

Repo **Actions → TE to Kindle → Run workflow**, pick a format and trigger. Wait 1–2 minutes; if you see `[done] sent` in the log, you're done — the file will land on your Kindle once it's online.

## Configuration

### Change the default format

Newer Kindles prefer epub. Edit `.github/workflows/te-to-kindle.yml`:

```yaml
TE_FORMAT: ${{ inputs.format || 'epub' }}   # change 'mobi' to 'epub'
```

### Change the schedule

Edit the cron in `.github/workflows/te-to-kindle.yml`. **Cron uses UTC** — subtract 8 hours from Beijing time:

```yaml
schedule:
  - cron: "10 1 * * 0"   # Sun 09:10 Beijing
  # - cron: "0 12 * * 0" # Sun 20:00 Beijing
```

GitHub-scheduled workflows may be delayed by a few minutes during peak hours; the built-in retry handles that.

## Layout

```
.
├── te_to_kindle.py                    # main script
├── requirements.txt                   # Python deps
├── last_sent.txt                      # last issue sent (auto-maintained)
└── .github/workflows/te-to-kindle.yml # GitHub Actions workflow
```

## How it works

1. **Compute target issue** — figure out this week's Saturday in Beijing time, which maps to the upstream `TE-YYYY-MM-DD/` folder
2. **Probe upstream** — query the GitHub API to check if the target folder is uploaded; retry every 10 min if not
3. **Download + email** — fetch the chosen format from `raw.githubusercontent.com`, attach to an email with subject `convert` (so Amazon auto-converts if needed), send via SMTP
4. **Record state** — write the issue ID to `last_sent.txt` and commit back; subsequent runs in the same week are no-ops

## Safety of going public

This repo is safe to make public:

- GitHub Secrets are automatically redacted in logs and unreadable from forks
- The workflow only responds to `schedule` and `workflow_dispatch`, so external PRs can't trigger it
- Actions on public repos are free and don't consume your private-repo minutes

One caveat: if you add `print` statements while debugging, **don't log emails, passwords, or other secrets** — public logs are visible to anyone.

## FAQ

**Q: My Kindle never received the file.**
- Confirm the sender is in Amazon's approved list
- Confirm the Kindle is online (Wi-Fi only models need a connection)
- Check the Actions log for SMTP errors (`535` usually means a wrong auth code)

**Q: Log says `not found upstream after 6 attempts`.**
- The upstream didn't publish this week, or the folder naming changed
- Manually check [evanbio/The_Economist](https://github.com/evanbio/The_Economist) for the current folder

**Q: How do I run it locally?**

```bash
pip install -r requirements.txt
export KINDLE_EMAIL=xxx@kindle.com
export SMTP_USER=you@gmail.com
export SMTP_PASS='your-app-password'
python te_to_kindle.py
```

**Q: How do I resend this week's issue?**
- Delete `last_sent.txt` from the repo and trigger the workflow again

## Credits

- Data source: [evanbio/The_Economist](https://github.com/evanbio/The_Economist)
- For personal study only. Please support the original publisher at [The Economist](https://www.economist.com/).

## License

MIT
