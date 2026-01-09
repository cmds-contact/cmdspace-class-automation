'use client';

import { IssueDocumentResponse } from '@/types';

interface ResultDisplayProps {
  result: IssueDocumentResponse;
  onReset: () => void;
}

export default function ResultDisplay({ result, onReset }: ResultDisplayProps) {
  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900">
          {result.isNewlyIssued ? '문서번호가 발급되었습니다' : '기존 문서번호 확인'}
        </h2>
        <p className="mt-2 text-gray-600">
          {result.isNewlyIssued
            ? '결제 확인서 문서번호가 성공적으로 발급되었습니다.'
            : '이미 발급된 문서번호입니다.'}
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
        <div className="flex justify-between items-center pb-4 border-b border-gray-200">
          <span className="text-gray-600">문서번호</span>
          <span className="text-xl font-mono font-bold text-blue-600">
            {result.documentNumber}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">발급일시</span>
          <span className="text-gray-900">{formatDate(result.issuedAt)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">상태</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            result.isNewlyIssued
              ? 'bg-green-100 text-green-800'
              : 'bg-blue-100 text-blue-800'
          }`}>
            {result.isNewlyIssued ? '신규 발급' : '재조회'}
          </span>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 text-sm">
          결제 확인서는 추후 입력하신 이메일로 발송될 예정입니다.
          문서번호를 기록해 두시기 바랍니다.
        </p>
      </div>

      <button
        onClick={onReset}
        className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition"
      >
        새로운 조회
      </button>
    </div>
  );
}
