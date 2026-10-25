# Treasury, MetaMask and realistic commercial pathway

The intended business beneficiary is **Alexander Viktorovich**. The economic accounts, marketplace profiles, invoices, wallets, credentials and proceeds are independent from IMPERIAL Core.

## The difference between a platform and a paying customer

The ten wired agent integrations (Albato, Aimylogic, TOMORU, TWIN, GigaChat, Yandex, Nodul, Bitrix24, MWS AI Agents, Cloud.ru) are primarily automation, AI or CRM platforms. They are not ten verified marketplaces that will generate client orders by themselves.

Revenue requires a separate lawful acquisition channel, approved accounts, real client demand, agreed terms, deliverables, acceptance and settlement. The product must not submit applications, send bulk unsolicited messages, accept contracts or claim earnings without appropriate brother authorization and provider approval.

## MetaMask is a destination preference, not payment support

A public EVM address may be recorded locally after the brother confirms he controls it; only address format can be checked automatically. Chain/network mismatch, fraud or mistaken address ownership can irreversibly lose funds.

**No seed phrases / private keys / signing prompts / token approvals / auto-transfers.** Do not route fiat-only marketplace payouts to a wallet by inventing transfer endpoints. Where the marketplace pays to a bank/card, the official settlement remains there and belongs to the brother. The brother independently decides on conversion or transfer within legal and provider terms.

## Evidence ledger

The standalone Python source kit includes `shpaizman/beneficiary.py` with a separate append-only SQLite hash-chain ledger that records **UNVERIFIED_EXTERNAL_CLAIM** and avoids fake balance assertions. Ledger integrity checks do not validate bank balances, block explorer receipts or actual cash settlement. This repo does not host user-specific financial data, addresses, statements or transaction IDs.

**Go-live gate:** obtain the brother's public payout destination and his explicit authorization on his own device, verify the particular provider's payout currency/network/fees with authoritative terms, then document *actual* settlement evidence. Until then: **PAYOUTS DISABLED, INCOME NOT VERIFIED**.
