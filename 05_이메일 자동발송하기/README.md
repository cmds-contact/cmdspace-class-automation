# Email Sender

Automated email sending system using [Resend](https://resend.com).

## Features

- Send single emails with HTML content
- Bulk email sending to multiple recipients
- TypeScript support with full type definitions
- Environment-based configuration

## Setup

### Prerequisites

- Node.js 18+
- Resend account with verified domain

### Installation

```bash
npm install
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```
RESEND_API_KEY=re_your_api_key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your Name
```

## Usage

### Basic Email

```typescript
import 'dotenv/config';
import { sendEmail } from './src/send-email.js';

await sendEmail({
  to: 'recipient@example.com',
  subject: 'Hello',
  html: '<h1>Welcome!</h1><p>This is a test email.</p>',
});
```

### Bulk Emails

```typescript
import 'dotenv/config';
import { sendBulkEmails } from './src/send-email.js';

const results = await sendBulkEmails(
  ['user1@example.com', 'user2@example.com'],
  {
    subject: 'Newsletter',
    html: '<h1>Monthly Update</h1>',
  }
);

results.forEach(({ email, result }) => {
  if (result instanceof Error) {
    console.error(`Failed to send to ${email}:`, result.message);
  } else {
    console.log(`Sent to ${email}, ID: ${result.id}`);
  }
});
```

### Run Test

```bash
npm run dev
```

## API Reference

### `sendEmail(options)`

Send a single email.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | `string \| string[]` | Yes | Recipient email(s) |
| `subject` | `string` | Yes | Email subject |
| `html` | `string` | Yes | HTML body |
| `text` | `string` | No | Plain text body |
| `replyTo` | `string` | No | Reply-to address |

**Returns**: `Promise<{ id: string }>`

### `sendBulkEmails(recipients, options)`

Send individual emails to multiple recipients.

| Parameter | Type | Description |
|-----------|------|-------------|
| `recipients` | `string[]` | List of email addresses |
| `options` | `Omit<EmailOptions, 'to'>` | Email options without `to` |

**Returns**: `Promise<Array<{ email: string; result: EmailResult | Error }>>`

## Project Structure

```
├── src/
│   ├── index.ts          # Entry point / test script
│   ├── send-email.ts     # Email sending functions
│   └── types.ts          # TypeScript type definitions
├── .env.example          # Environment template
├── .gitignore
├── package.json
├── tsconfig.json
└── README.md
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Run with tsx (development) |
| `npm run build` | Compile TypeScript |
| `npm run start` | Run compiled code |
| `npm run typecheck` | Type checking only |

## License

Private
