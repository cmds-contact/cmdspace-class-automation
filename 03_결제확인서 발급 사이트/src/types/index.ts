// API Request/Response Types
export interface IssueDocumentRequest {
  email: string;
  name: string;
  orderNumber: string;
  deliveryEmail: string;
}

export interface IssueDocumentResponse {
  success: true;
  documentNumber: string;
  issuedAt: string;
  isNewlyIssued: boolean;
}

export interface ErrorResponse {
  success: false;
  error: string;
  code: 'VALIDATION_ERROR' | 'NOT_FOUND' | 'AIRTABLE_ERROR' | 'INTERNAL_ERROR';
}

export type ApiResponse = IssueDocumentResponse | ErrorResponse;

// Airtable Types
export interface AirtableRecord {
  id: string;
  fields: Record<string, unknown>;
}

export interface MemberProductsRecord extends AirtableRecord {
  fields: {
    'MemberProducts Code': string;
    'E-mail (from Member)': string[];
    'Name (from Member)': string[];
    'Order Number (from Orders)'?: string[];
    [key: string]: unknown;
  };
}

export interface DocumentIssuanceRecord extends AirtableRecord {
  fields: {
    document_number: string;
    order_number: string;
    input_email: string;
    input_name: string;
    delivery_email: string;
    issued_at: string;
  };
}
