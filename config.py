"""Weekly Agent 설정"""

# 주간 카테고리
WEEKLY_CATEGORIES = ["거시경제", "개별 산업", "개별 기업", "금융", "M&A", "PE", "VC"]

# GitHub Pages 소스 URL
NEWS_GHPAGES_BASE = "https://oooohhhhiiii.github.io/daily-news-agent"
BLOG_GHPAGES_BASE = "https://oooohhhhiiii.github.io/daily-blog-agent"
YOUTUBE_GHPAGES_BASE = "https://oooohhhhiiii.github.io/daily-youtube-agent"
WEEKLY_GHPAGES_BASE = "https://oooohhhhiiii.github.io/weekly-agent"

# Daily News 카테고리별 파일명 접두사
NEWS_FILES = [
    "NaverNews_macro", "NaverNews_ma", "NaverNews_pe", "NaverNews_vc", "NaverNews_stock",
    "TheBell_deal", "TheBell_finance", "TheBell_invest", "TheBell_industry",
]

# 카테고리별 색상 (카드뉴스용)
CATEGORY_COLORS = {
    "거시경제": "#2563eb",
    "개별 산업": "#059669",
    "개별 기업": "#7c3aed",
    "금융": "#dc2626",
    "M&A": "#d97706",
    "PE": "#0891b2",
    "VC": "#be185d",
}

# 카테고리별 이모지
CATEGORY_EMOJI = {
    "거시경제": "🌍",
    "개별 산업": "🏭",
    "개별 기업": "🏢",
    "금융": "💰",
    "M&A": "🤝",
    "PE": "📊",
    "VC": "🚀",
}

# Telegram API
TELEGRAM_API_URL = "https://api.telegram.org"

# 데이터 수집 설정
FETCH_DAYS = 5          # 수집할 일 수
MIN_DAYS_REQUIRED = 2   # 최소 필요 일 수

# HTTP 요청 설정
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
