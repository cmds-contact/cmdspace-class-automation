# Payment Confirmation Document Issuance System

A PoC (Proof of Concept) web application for issuing payment confirmation document numbers for CMDSPACE course members.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: Airtable
- **Deployment**: Vercel (planned)

## Features

- User input form (email, name, order number, delivery email)
- Order validation against Airtable (Orders table, valid_orders view)
- Document number generation (format: `CPC-YYYYMM-XXX`)
- Duplicate request handling (returns existing document number)
- Document issuance record storage in Airtable

## Project Structure

```
src/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Main page with form
│   ├── globals.css             # Global styles
│   └── api/
│       └── issue-document/
│           └── route.ts        # API endpoint
├── components/
│   ├── PaymentVerificationForm.tsx  # Input form component
│   └── ResultDisplay.tsx            # Result display component
├── lib/
│   ├── airtable.ts             # Airtable API client
│   └── document-number.ts      # Document number generation
└── types/
    └── index.ts                # TypeScript type definitions
```

## API Endpoint

### POST /api/issue-document

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "orderNumber": "O26010815195326200O2",
  "deliveryEmail": "user@example.com"
}
```

**Success Response:**
```json
{
  "success": true,
  "documentNumber": "CPC-202601-001",
  "issuedAt": "2026-01-08T21:55:18.317Z",
  "isNewlyIssued": true
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "No matching order found. Please check your information.",
  "code": "NOT_FOUND"
}
```

## Validation Logic

1. Query Orders table (valid_orders view) in Airtable
2. Match all three fields exactly:
   - Order Number
   - E-mail
   - Name
3. If match found and no existing document number, generate new one
4. If document number already exists, return existing one
5. Record issuance info in DocumentIssuance table

## Document Number Format

- Format: `CPC-YYYYMM-XXX`
- Example: `CPC-202601-001`
- Sequential numbering per month
- One document number per order (reused on duplicate requests)

## Airtable Schema

### Orders Table (valid_orders view)
- `Order Number` - Unique order identifier
- `E-mail` - Customer email
- `Name` - Customer name

### DocumentIssuance Table
| Field | Type | Description |
|-------|------|-------------|
| document_number | Text | CPC-YYYYMM-XXX format |
| order_number | Text | Associated order number |
| input_email | Email | Submitted email |
| input_name | Text | Submitted name |
| delivery_email | Email | Delivery email for document |
| issued_at | DateTime | Issuance timestamp |

## Environment Variables

```bash
AIRTABLE_API_KEY=pat_xxxxxxxxxxxx
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Local Testing

```bash
# Start dev server on port 3001 (if 3000 is occupied)
npm run dev -- -p 3001

# Test API
curl -X POST http://localhost:3001/api/issue-document \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","orderNumber":"OXXXXXXXXX","deliveryEmail":"test@test.com"}'
```

## Out of Scope (PoC)

- PDF generation
- Email delivery
- User authentication
- Rate limiting
- Refund invalidation handling
