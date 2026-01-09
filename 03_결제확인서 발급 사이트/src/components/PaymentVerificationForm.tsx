'use client';

import { useState, FormEvent } from 'react';
import { IssueDocumentRequest, ApiResponse, IssueDocumentResponse } from '@/types';
import ResultDisplay from './ResultDisplay';

export default function PaymentVerificationForm() {
  const [formData, setFormData] = useState<IssueDocumentRequest>({
    email: '',
    name: '',
    orderNumber: '',
    deliveryEmail: '',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IssueDocumentResponse | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
      // 결제 이메일 입력 시 수령 이메일도 자동 입력 (비어있으면)
      ...(name === 'email' && !formData.deliveryEmail ? { deliveryEmail: value } : {}),
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/issue-document', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data: ApiResponse = await response.json();

      if (data.success) {
        setResult(data);
      } else {
        setError(data.error);
      }
    } catch {
      setError('네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      email: '',
      name: '',
      orderNumber: '',
      deliveryEmail: '',
    });
    setResult(null);
    setError(null);
  };

  if (result) {
    return <ResultDisplay result={result} onReset={handleReset} />;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          결제 시 사용한 이메일
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          placeholder="example@email.com"
        />
      </div>

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          결제자 성함
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          placeholder="홍길동"
        />
      </div>

      <div>
        <label htmlFor="orderNumber" className="block text-sm font-medium text-gray-700 mb-1">
          주문번호
        </label>
        <input
          type="text"
          id="orderNumber"
          name="orderNumber"
          value={formData.orderNumber}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          placeholder="O250101123456789ABC"
        />
        <p className="mt-1 text-sm text-gray-500">
          마이페이지 &gt; 결제내역에서 확인할 수 있습니다.
        </p>
      </div>

      <div>
        <label htmlFor="deliveryEmail" className="block text-sm font-medium text-gray-700 mb-1">
          결제 확인서 수령용 이메일
        </label>
        <input
          type="email"
          id="deliveryEmail"
          name="deliveryEmail"
          value={formData.deliveryEmail}
          onChange={handleChange}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
          placeholder="example@email.com"
        />
        <p className="mt-1 text-sm text-gray-500">
          결제 이메일과 다른 이메일로 받으실 수 있습니다.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            처리 중...
          </span>
        ) : (
          '문서번호 발급 요청'
        )}
      </button>
    </form>
  );
}
