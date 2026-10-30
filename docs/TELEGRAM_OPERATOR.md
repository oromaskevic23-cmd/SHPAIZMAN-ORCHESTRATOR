# SHPAIZMAN — Telegram Operator Channel (read-only)

**Scope:** brother-owned, local SHPAIZMAN Service Factory only. This integration is not remote access to the beneficiary's Windows machine or the separately distributed full 0.8.0 RC1 ZIP. No production Telegram connection has been verified by GitHub. The Bot API requires outbound HTTPS to api.telegram.org; no incoming ports or public webhook endpoints are needed.

## Security prerequisite: revoke any disclosed token

If a Telegram BotFather token was pasted into any chat, issue, commit, screenshot, or document, consider it exposed. In Telegram open [@BotFather](https://t.me/BotFather), choose the intended bot and **revoke the old token and generate a new one**, using BotFather's current menu or revoke flow. Do not use the disclosed token again. Do not post the replacement in chats, tickets, GitHub or screenshots.

All steps on the beneficiary's PC require his consent. Never embed the token into the repository, a tracked .env file, a command-line argument or an example URL. Only use it as a temporary local environment variable supplied by secure console prompt.

## Implemented read-only functions

| Command | Effect |
| --- | --- |
| /start, /help | Lists safe commands |
| /ping | Bot process responsiveness; **not** Windows or NCA health |
| /status | Aggregate local Service Factory pipeline; no customer records |
| /services | Five predefined offline IT service packages |
| /verify | Local SQLite audit-chain check, **not** an external financial proof |

All other commands are ignored. **No Telegram approval, remote shell, agent execution, lead creation, payment, wallet signing, customer data access or unsolicited messaging is present.** Authorized commands are limited to private chat IDs matching the sender's numeric Telegram user ID. An empty/malformed allowlist prevents startup. Unauthorized chats receive no response. Network error descriptions are suppressed to avoid revealing token-bearing Telegram URLs.

## Authorized Windows 10/11 setup

Requirements: Python 3.12, checked-out repository, outbound HTTPS and a newly rotated BotFather token. Run the following in PowerShell from the repository root. Python standard library only, no pip packages needed.

~~~powershell
# 1. On the beneficiary's authorized Windows PC:
$secureToken = Read-Host "Paste NEW Telegram token privately" -AsSecureString
$env:SHPAIZMAN_TELEGRAM_BOT_TOKEN = [System.Net.NetworkCredential]::new("", $secureToken).Password
try {
    # 2. Validate token and check for conflicts with any existing webhook.
    py -3.12 -m shpaizman.telegram_bot --check
    if ($LASTEXITCODE -ne 0) { throw "Telegram preflight blocked" }

    # 3. Beneficiary sends /start to this bot in a PRIVATE Telegram chat.
    # Print candidate IDs locally; independently confirm the correct owner.
    py -3.12 -m shpaizman.telegram_bot --discover-chat-ids
    if ($LASTEXITCODE -ne 0) { throw "Chat ID discovery blocked" }

    # 4. Set only beneficiary's verified private numeric Telegram ID.
    $env:SHPAIZMAN_TELEGRAM_CHAT_IDS = Read-Host "Verified private Telegram chat ID"

    # 5. Start read-only long polling. Ctrl+C stops the bot.
    py -3.12 -m shpaizman.telegram_bot
} finally {
    Remove-Item Env:SHPAIZMAN_TELEGRAM_BOT_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:SHPAIZMAN_TELEGRAM_CHAT_IDS -ErrorAction SilentlyContinue
}
~~~

If discovery does not show /start, send it again and retry. A chat ID appearing in updates **does not prove identity or authorize access**. Independently verify it with the beneficiary. Never allowlist unknown senders. For multiple authorized private chats, use comma-separated numeric IDs.

## Polling and other providers

Telegram supports either polling or an active webhook, not both. The module intentionally **never calls deleteWebhook**; it refuses to start if a webhook is configured, preserving existing integrations. Use only one polling process per bot. No Windows service/autostart is installed by the repository; an authorized operator must keep the process running or arrange a supervised deployment.

## Reproducible tests and known limitations

~~~powershell
py -3.12 -m unittest discover -s tests -v
~~~

Expected initial /status in an empty local database: Orders 0; external accounts, agent runtime and revenue **NOT VERIFIED**. /ping only demonstrates the Telegram process replied. This public repository does not include the separate full Windows source ZIP, and this adapter does **not** control the ten agents. A future approved extension would require independently authenticated actions, evidence and strict owner approval. A Telegram response does not establish that SHPAIZMAN is running continuously, that services were sold or that payment was received.

**Security boundaries:** independent beneficiary; FREE_ONLY; explicit owner authorization; least privilege; fail closed; no IMPERIAL Core secrets or wallets. See SECURITY.md.

Official Telegram Bot API: https://core.telegram.org/bots/api — getMe, getUpdates, sendMessage, getWebhookInfo.
