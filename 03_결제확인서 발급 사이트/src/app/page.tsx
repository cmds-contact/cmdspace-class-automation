import PaymentVerificationForm from '@/components/PaymentVerificationForm';

export default function Home() {
  return (
    <main className="min-h-screen py-12 px-4">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            결제 확인서 발급
          </h1>
          <p className="text-gray-600">
            CMDSPACE 강의 결제 확인서 문서번호를 발급받으세요.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8">
          <PaymentVerificationForm />
        </div>

        <footer className="mt-8 text-center text-sm text-gray-500">
          <p>문의사항이 있으시면 고객센터로 연락해 주세요.</p>
        </footer>
      </div>
    </main>
  );
}
