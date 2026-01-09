# API 이메일 서비스 상세 비교

> AWS SES, SendGrid, Mailgun, Postmark, Resend 심층 분석

---

## 1. AWS SES (Simple Email Service)

### 개요
Amazon Web Services에서 제공하는 클라우드 기반 이메일 발송 서비스

### 가격 정책
| 항목 | 비용 |
|------|------|
| EC2에서 발송 | 1,000건당 $0.10 |
| 외부에서 발송 | 1,000건당 $0.10 |
| 첨부파일 | GB당 $0.12 |
| **월 10,000건** | **~$1** |

> 2025년 7월 15일부터 신규 고객은 최대 $200 AWS 프리 티어 크레딧 제공

### 장점
- **최저가**: 대량 발송 시 압도적 비용 효율
- **높은 전달률**: SendGrid 대비 16.1% 높은 받은 편지함 배치율
- **AWS 생태계 연동**: Lambda, SNS, CloudWatch 등과 통합
- **한글 문서 제공**: 공식 한국어 문서 지원

### 단점
- **설정 복잡**: 개발자 지향적, AWS Console/SDK 필수
- **마케팅 기능 없음**: 순수 발송 기능만 제공
- **반송 처리 별도 구현**: 반송 이메일 처리 자동화 필요

### 적합한 경우
- AWS 인프라 이미 사용 중
- 대량 트랜잭션 이메일 발송
- 비용이 최우선

### 코드 예시 (Python boto3)
```python
import boto3

ses = boto3.client('ses', region_name='ap-northeast-2')

response = ses.send_email(
	Source='sender@example.com',
	Destination={
		'ToAddresses': ['recipient@example.com']
	},
	Message={
		'Subject': {'Data': '결제 확인서'},
		'Body': {
			'Html': {'Data': '<h1>결제가 완료되었습니다</h1>'}
		}
	}
)
```

---

## 2. SendGrid (Twilio)

### 개요
2009년 설립, 현재 Twilio 소속. 트랜잭션 + 마케팅 이메일 모두 지원

### 가격 정책
| 플랜 | 월 이메일 | 비용 |
|------|----------|------|
| Free | 100/일 (60일 한정) | $0 |
| Essentials | 50,000 | $19.95 |
| Pro | 100,000 | $89.95 |
| **월 10,000건** | - | **$15~20** |

### 장점
- **사용 편의성**: 즉시 도메인/이메일 승인
- **마케팅 기능 포함**: 캠페인, 템플릿 빌더
- **SMS/WhatsApp 연동**: Twilio 통합

### 단점
- **고객지원 이슈**: Twilio 인수 후 지원 품질 저하 보고
- **프리미엄 지원 별도 비용**: 고급 지원은 상위 플랜만
- **무료 플랜 60일 한정**: 이후 유료 전환 필수

### 적합한 경우
- 트랜잭션 + 마케팅 단일 서비스 원할 때
- 빠른 시작이 필요할 때

### 코드 예시 (Python)
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
	from_email='sender@example.com',
	to_emails='recipient@example.com',
	subject='결제 확인서',
	html_content='<h1>결제가 완료되었습니다</h1>'
)

sg = SendGridAPIClient('YOUR_API_KEY')
response = sg.send(message)
```

---

## 3. Mailgun

### 개요
개발자 친화적 이메일 API 서비스, 강력한 분석 도구 제공

### 가격 정책
| 플랜 | 월 이메일 | 비용 |
|------|----------|------|
| Flex (무료) | 100/일 무기한 | $0 |
| Foundation | 10,000 | $35 |
| Scale | 100,000 | $90 |
| **월 10,000건** | - | **$35** |

### 장점
- **무료 플랜 무기한**: 일 100건 영구 무료
- **99.99% 가동시간 SLA**: 안정성 보장
- **강력한 분석**: 상세 통계 및 검증 도구
- **이메일 검증 API**: 유효 이메일 확인 기능

### 단점
- **상대적 고가**: 같은 볼륨에서 타 서비스보다 비쌈
- **영문 문서만**: 한글 지원 없음

### 적합한 경우
- 이메일 검증이 중요할 때
- 안정성이 최우선일 때

### 코드 예시 (Python)
```python
import requests

response = requests.post(
	'https://api.mailgun.net/v3/YOUR_DOMAIN/messages',
	auth=('api', 'YOUR_API_KEY'),
	data={
		'from': 'sender@example.com',
		'to': 'recipient@example.com',
		'subject': '결제 확인서',
		'html': '<h1>결제가 완료되었습니다</h1>'
	}
)
```

---

## 4. Postmark

### 개요
트랜잭션 이메일 전문 서비스, 최고 수준의 전달률

### 가격 정책
| 월 이메일 | 비용 |
|----------|------|
| 10,000 | $15 |
| 50,000 | $55 |
| 125,000 | $105 |

### 장점
- **최고 전달률 93.8%**: 테스트 결과 업계 최고
- **동일한 고객지원**: 모든 플랜에서 동일 수준 지원
- **45일 메시지 기록**: 무료로 45일간 이벤트/컨텐츠 보관
- **빠른 전송**: 평균 10초 내 전달

### 단점
- **마케팅 기능 없음**: 트랜잭션 전용
- **영문 문서만**: 한글 지원 없음

### 적합한 경우
- 전달률이 가장 중요할 때
- 트랜잭션 이메일 전용일 때
- 결제 확인서, 비밀번호 재설정 등

### 코드 예시 (Python)
```python
from postmarker.core import PostmarkClient

postmark = PostmarkClient(server_token='YOUR_TOKEN')
postmark.emails.send(
	From='sender@example.com',
	To='recipient@example.com',
	Subject='결제 확인서',
	HtmlBody='<h1>결제가 완료되었습니다</h1>'
)
```

---

## 5. Resend

### 개요
2022년 설립, "이메일의 Stripe"를 표방하는 개발자 중심 서비스

### 가격 정책
| 월 이메일 | 비용 |
|----------|------|
| 100/일 (무료) | $0 |
| 50,000 | $20 |
| 100,000 | $45 |

### 장점
- **최고의 개발자 경험**: "Mailgun, SendGrid, Mandrill과 비교할 수 없는 DX"
- **React Email**: HTML 대신 React 컴포넌트로 이메일 작성
- **Batch API**: 한 번에 100개 이메일 발송
- **다양한 SDK**: Python, Ruby, PHP, Go, Java, Rust 등

### 단점
- **신생 서비스**: 2022년 설립, 안정성 검증 중
- **마케팅 기능 제한**: 기본적인 기능만 제공
- **간헐적 지연 보고**: 일부 사용자 20분+ 지연 경험

### 2024년 주요 업데이트
- React Email v3.0: 54개 컴포넌트, 40배 성능 향상
- Batch API 출시
- Rust SDK 추가

### 적합한 경우
- 개발자 경험이 중요할 때
- React 사용에 익숙할 때
- 모던한 개발 환경 선호 시

### 코드 예시 (Python)
```python
import resend

resend.api_key = "YOUR_API_KEY"

params = {
	"from": "sender@example.com",
	"to": ["recipient@example.com"],
	"subject": "결제 확인서",
	"html": "<h1>결제가 완료되었습니다</h1>",
}

email = resend.Emails.send(params)
```

### React Email 예시
```jsx
import { Html, Button, Text } from '@react-email/components';

export default function PaymentConfirmation({ amount }) {
	return (
		<Html>
			<Text>결제가 완료되었습니다</Text>
			<Text>결제 금액: {amount}원</Text>
			<Button href="https://example.com/receipt">
				영수증 확인
			</Button>
		</Html>
	);
}
```

---

## 종합 비교표

| 항목 | AWS SES | SendGrid | Mailgun | Postmark | Resend |
|------|---------|----------|---------|----------|--------|
| **설립** | 2011 | 2009 | 2010 | 2010 | 2022 |
| **월 10K 비용** | ~$1 | $15~20 | $35 | $15 | $20 |
| **무료 플랜** | 제한적 | 60일 | 무기한 | 100/월 | 100/일 |
| **전달률** | 높음 | 중상 | 중상 | **최고** | 높음 |
| **설정 난이도** | 어려움 | 쉬움 | 보통 | 쉬움 | 쉬움 |
| **개발자 경험** | 보통 | 좋음 | 좋음 | 좋음 | **최고** |
| **마케팅 기능** | ❌ | ✅ | 제한적 | ❌ | 제한적 |
| **한글 문서** | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 결론: 상황별 추천

| 상황 | 추천 서비스 | 이유 |
|------|------------|------|
| 비용 최소화 | **AWS SES** | 월 $1 이하 |
| 전달률 최우선 | **Postmark** | 93.8% 전달률 |
| 개발 편의성 | **Resend** | React Email, 최고 DX |
| 마케팅 포함 | **SendGrid** | 올인원 솔루션 |
| 안정성 | **Mailgun** | 99.99% SLA |

---

## 참고 링크

- [AWS SES 공식](https://aws.amazon.com/ses/)
- [SendGrid 공식](https://sendgrid.com/)
- [Mailgun 공식](https://www.mailgun.com/)
- [Postmark 공식](https://postmarkapp.com/)
- [Resend 공식](https://resend.com/)
- [Postmark 트랜잭션 이메일 비교](https://postmarkapp.com/blog/transactional-email-providers)
- [Email APIs in 2025 비교](https://medium.com/@nermeennasim/email-apis-in-2025-sendgrid-vs-resend-vs-aws-ses-a-developers-journey-8db7b5545233)
