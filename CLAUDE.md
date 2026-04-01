# Weekly Agent

최근 5일치 Daily 뉴스레터(News, Blog, YouTube)를 분석하여 주간 브리핑 뉴스레터 + 카드뉴스를 생성하고 배포하는 에이전트.

## 주간 카테고리 (7개)
- **거시경제**: 금리, 환율, GDP, 물가, 통화정책, 국제경제, 무역
- **개별 산업**: 산업 동향, 섹터별 이슈, 규제 변화, 기술 트렌드
- **개별 기업**: 특정 기업 실적, 경영 이슈, 인사, 전략 변화
- **금융**: 은행, 증권, 보험, 핀테크, 금융 규제, 자본시장
- **M&A**: 인수합병, 매각, 경영권 분쟁, 합병 심사
- **PE**: 사모펀드, 바이아웃, PEF 투자·회수, LP/GP 동향
- **VC**: 벤처캐피탈, 스타트업 투자, 시리즈 펀딩, IPO

## 주간 워크플로우

### Step 1: 데이터 수집
```bash
PYTHONIOENCODING=utf-8 python fetch_weekly_data.py
```
- 3개 소스(News, Blog, YouTube)의 GitHub Pages HTML을 가져와 파싱
- 최근 5일치 자동 계산 (어제 기준 역산)
- 결과: `output/weekly_raw_YYYYMMDD.json`
- 수집된 날짜가 3일 미만이면 중단

### Step 2: 카테고리 분류 및 분석
- `output/weekly_raw_YYYYMMDD.json` 파일을 읽는다
- 모든 아이템을 7개 주간 카테고리로 재분류한다:
  - 하나의 기사가 여러 카테고리에 해당할 수 있으면 가장 적합한 1개로 분류
  - 분류가 애매한 경우 제목과 요약 내용을 기반으로 판단
- 카테고리별로 핵심 이슈를 3~5개 도출한다:
  - 여러 기사에서 반복 언급되는 주제를 우선
  - 뉴스/블로그/유튜브 교차 언급 토픽을 식별
  - 각 이슈에 관련 기사 제목들을 매핑
- 결과를 `output/weekly_analysis_YYYYMMDD.json`으로 저장한다

분석 JSON 형식:
```json
{
  "period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "categories": {
    "거시경제": {
      "key_issues": [
        {
          "title": "이슈 제목",
          "description": "1~2문장 요약",
          "related_articles": ["기사1 제목", "기사2 제목"],
          "sources": ["news", "youtube"]
        }
      ],
      "source_counts": {"news": 15, "blog": 3, "youtube": 2}
    }
  }
}
```

### Step 3: 주간 뉴스레터 작성
- `output/weekly_analysis_YYYYMMDD.json`을 기반으로 줄글 형식의 주간 분석을 작성한다
- 구조:

```markdown
# 주간 브리핑 (MM/DD ~ MM/DD)

이번 주 시장의 핵심 흐름 요약 도입부 (200~300자)

## 거시경제
### 핵심 이슈 1 제목
분석 2~3단락. 뉴스/블로그/유튜브 소스를 교차 참조.
### 핵심 이슈 2 제목
...

## 개별 산업
...

## 개별 기업
...

## 금융
...

## M&A
...

## PE
...

## VC
...

다음 주 주목할 이슈 마무리 (100~200자)
```

- 작성 규칙:
  - 한국어, ~다 체, 전문적·분석적 톤
  - 카테고리별 2~4개 핵심 이슈, 각 150~400자 분석
  - 복수 소스 교차 참조 시 출처 명시
  - 타겟 분량: 5,000~8,000자
  - 단순 나열이 아닌 종합 분석 (트렌드, 의미, 시사점)
- 결과: `output/weekly_newsletter_YYYYMMDD.md`

### Step 4: HTML 생성
```bash
PYTHONIOENCODING=utf-8 python html_newsletter.py --date YYMMDD
PYTHONIOENCODING=utf-8 python html_cardnews.py --date YYMMDD
```
- 뉴스레터 마크다운 → `output/WeeklyNewsletter_YYMMDD.html`
- 분석 JSON → `output/WeeklyCardNews_YYMMDD.html`
- YYMMDD는 수집 기간의 마지막 날짜 (예: 260331)

### Step 5: Telegram 전송 및 GitHub Pages 배포
```bash
PYTHONIOENCODING=utf-8 python telegram_send.py --document output/WeeklyNewsletter_YYMMDD.html "📊 주간 브리핑 뉴스레터 (MM/DD~MM/DD)"
PYTHONIOENCODING=utf-8 python telegram_send.py --document output/WeeklyCardNews_YYMMDD.html "📊 주간 브리핑 카드뉴스 (MM/DD~MM/DD)"
PYTHONIOENCODING=utf-8 python publish_ghpages.py --date YYMMDD
```
- publish_ghpages.py 실행 결과로 GitHub Pages URL이 JSON으로 출력됨

### Step 6: Notion 아카이브 저장
- `.env` 파일에서 `NOTION_PAGE_ID`를 읽는다
- Notion MCP의 `notion-create-pages` 도구를 사용하여 서브 페이지 생성:
  - **페이지 제목**: "YYYY-MM-DD Weekly Briefing (MM/DD~MM/DD)"
  - **페이지 내용**:
    - 주간 뉴스레터 GitHub Pages 링크
    - 카드뉴스 GitHub Pages 링크
    - 카테고리별 핵심 이슈 요약 (불릿 리스트)

## 주의사항
- 모든 스크립트는 프로젝트 루트 디렉토리에서 실행
- YYMMDD 날짜는 수집 기간의 마지막 날짜
- 뉴스레터와 카드뉴스 모두 한국어로 작성
- 카테고리 분류가 애매한 경우 내용의 핵심 주제를 기준으로 판단
- GitHub Pages 배포 실패 시 Notion 저장은 건너뜀
- Telegram 전송 실패 시에도 GitHub Pages 배포는 계속 진행
