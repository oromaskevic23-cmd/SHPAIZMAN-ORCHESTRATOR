# Security policy — SHPAIZMAN Brother Edition

**Scope:** only the brother-owned SHPAIZMAN source and authorized accounts. **No rights to access the user's computer, third-party accounts, wallets, financial systems or IMPERIAL Core production are granted by this repository.**

## Zero-Trust operating invariants

- Identity is not authority. A collaborator, agent, chatbot or GitHub connection is never permission to operate on the brother's Windows device.
- FREE_ONLY: no subscriptions, pay-per-use APIs, cloud inference or overage without explicit brother consent and verified zero-cost entitlement.
- All external platform actions must use published authorized APIs with account-local grants, timeouts, operation allowlists and logs. Disallow credential exfiltration, messaging without consent, false traffic, fake reviews and Terms circumvention.
- The brother approves all installation, account connections, contracts, payments and wallet actions **on his own device**. Keep Windows security protections unchanged. No privilege escalation or arbitrary remote shell.
- Never collect, log or transmit MetaMask recovery phrases, wallet/private signing keys, security codes, webhook signing secrets or payment credentials. Only public address strings may be stored as preferences.
- No payout automation or automatic on-chain transfer is shipped. An address format validation does not prove account ownership, payouts, revenue or a successful transfer.
- Changes to shared repositories cannot change beneficiary rights or payment destinations without an explicit owner-approved contractual change.
- If any prerequisite cannot be verified, stop the operation and state **BLOCKED**. Keep audit and rollback evidence; do not turn failed checks into a claimed success.

## Dependency/provenance boundary

The original donor ZIP is external to this repo and must be independently supplied and SHA-256 matched. `enterprise.verify_release` checks *file consistency* without executing code. It is not a signature by the original author or malware certification. No public Git history bundle, recovered scripts, credentials or executable artifacts should be uploaded without separate review.

## Responsible disclosure

Do not open public issues containing keys, seed phrases, identity documents or real provider vulnerabilities. Use GitHub's private vulnerability-reporting channel when available, or establish a separately verified private channel with the maintainer. No bug bounty, response SLA or security certification is promised.
