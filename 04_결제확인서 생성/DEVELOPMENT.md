# Payment Confirmation PDF Generator

## Overview

This project generates bilingual (Korean/English) payment confirmation PDFs and uploads them to Cloudflare R2 for secure distribution to customers.

## Architecture

```
HTML Template → PDF → Cloudflare R2 → Public URL → Customer Email
```

## Cloudflare R2 Configuration

### Bucket Information

| Property | Value |
|----------|-------|
| Bucket Name | `payment-confirmations` |
| Public URL Base | `https://pub-71bab14911324382a16a4f5cb2a8c58a.r2.dev` |
| Public Access | Enabled |

### File Naming Convention

Files are uploaded with UUID-based filenames to prevent URL guessing:

```
{uuid}.pdf
```

Example: `eddf24c7-2bbe-46a4-8bd4-b90731cbb59b.pdf`

## CLI Commands

### Prerequisites

```bash
npm install -g wrangler
wrangler login
```

### Upload a PDF

```bash
# Generate UUID and upload
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
wrangler r2 object put "payment-confirmations/${UUID}.pdf" \
  --file="path/to/file.pdf" \
  --content-type="application/pdf" \
  --remote

# Public URL will be:
# https://pub-71bab14911324382a16a4f5cb2a8c58a.r2.dev/${UUID}.pdf
```

### List Buckets

```bash
wrangler r2 bucket list
```

### Check Bucket Info

```bash
wrangler r2 bucket info payment-confirmations
```

### Download a File

```bash
wrangler r2 object get payment-confirmations/{filename}.pdf --remote
```

### Delete a File

```bash
wrangler r2 object delete payment-confirmations/{filename}.pdf --remote
```

## HTML Template

The payment confirmation template (`payment_confirmation_bilingual_v1.html`) includes:

- **Header**: Document title in Korean/English
- **Document Info**: Document number, issue date, order number
- **Order Details**: Product name, code, amount
- **Payment Information**: Payment date, method, type, total amount
- **Payer Information**: Name, phone, email
- **Seller Information**: Business name, website, contact
- **Signature/Stamp**: Company seal
- **Footer**: Legal disclaimer

### Template Variables

| Field | ID | Description |
|-------|-----|-------------|
| Document Number | `documentNumber` | e.g., CPC-202601-001 |
| Issue Date | `issueDate` | e.g., 2026-01-01 |
| Order Number | `orderNumber` | e.g., ORD-20240101-001 |
| Payment Date | `paymentDate` | e.g., 2024-01-01 14:30:00 |
| Payment Method | `paymentMethod` | e.g., Credit Card |
| Payment Type | `paymentType` | e.g., One-time payment |
| Payment Amount | `paymentAmount` | e.g., 99,000 KRW |
| Student Name | `studentName` | Customer name |
| Student Phone | `studentPhone` | Customer phone |
| Student Email | `studentEmail` | Customer email |

## Security Model

- **Access Control**: Security through obscurity (UUID-based URLs)
- **URL Format**: Random UUID makes URLs unguessable
- **Risk Level**: Low (payment confirmations, not sensitive financial data)
- **Acceptable Risk**: URL sharing by recipient is acceptable

## Future Improvements

- [ ] Automated PDF generation from order data
- [ ] Email integration for automatic sending
- [ ] Custom domain (e.g., `files.cmdspace.kr`)
- [ ] Signed URLs with expiration for higher security needs
