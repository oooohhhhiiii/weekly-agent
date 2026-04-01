"""주간 분석 JSON을 카드뉴스 HTML로 변환"""

import sys
import json
import html
from pathlib import Path

from config import CATEGORY_COLORS, CATEGORY_EMOJI, WEEKLY_CATEGORIES

OUTPUT_DIR = Path(__file__).parent / "output"


def render_category_card(category, data):
    """단일 카테고리 카드 렌더링"""
    color = CATEGORY_COLORS.get(category, "#333")
    emoji = CATEGORY_EMOJI.get(category, "📌")
    cat_html = html.escape(category)

    # 핵심 이슈 불릿 포인트
    issues = data.get("key_issues", [])
    bullets_html = ""
    for issue in issues[:5]:
        title = html.escape(issue.get("title", ""))
        desc = html.escape(issue.get("description", ""))
        bullets_html += f"""
        <div style="margin:8px 0; padding:8px 12px; background:#f8f9fa; border-radius:8px;">
          <p style="margin:0 0 4px; font-size:14px; font-weight:600; color:#1a1a2e;">{title}</p>
          <p style="margin:0; font-size:13px; color:#555; line-height:1.5;">{desc}</p>
        </div>"""

    # 소스 카운트
    source_counts = data.get("source_counts", {})
    news_cnt = source_counts.get("news", 0)
    blog_cnt = source_counts.get("blog", 0)
    yt_cnt = source_counts.get("youtube", 0)
    count_parts = []
    if news_cnt:
        count_parts.append(f"뉴스 {news_cnt}건")
    if blog_cnt:
        count_parts.append(f"블로그 {blog_cnt}건")
    if yt_cnt:
        count_parts.append(f"유튜브 {yt_cnt}건")
    count_str = " / ".join(count_parts) if count_parts else ""

    count_html = ""
    if count_str:
        count_html = f"""
      <div style="margin-top:8px; text-align:right;">
        <span style="font-size:11px; color:#999; background:#f0f0f0; padding:3px 8px; border-radius:10px;">{html.escape(count_str)}</span>
      </div>"""

    return f"""
    <div style="background:#fff; border-radius:12px; margin-bottom:12px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <div style="border-left:4px solid {color}; padding:16px 20px;">
        <h3 style="margin:0 0 8px; font-size:17px; color:{color};">{emoji} {cat_html}</h3>{bullets_html}{count_html}
      </div>
    </div>"""


def render_cardnews_html(title, period_start, period_end, categories_data):
    """카드뉴스 전체 HTML 렌더링"""
    title_html = html.escape(title)
    period_str = f"{period_start} ~ {period_end}"

    # 카테고리별 카드 생성
    cards_html = ""
    for cat in WEEKLY_CATEGORIES:
        if cat in categories_data:
            cards_html += render_category_card(cat, categories_data[cat])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_html}</title>
</head>
<body style="margin:0; padding:16px; background:#f0f2f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;">
  <div style="max-width:640px; margin:0 auto;">
    <div style="background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color:#fff; padding:24px; border-radius:12px; margin-bottom:12px; text-align:center;">
      <h1 style="margin:0; font-size:22px; font-weight:700;">&#128202; {title_html}</h1>
      <p style="margin:8px 0 0; font-size:14px; color:rgba(255,255,255,0.7);">{html.escape(period_str)}</p>
    </div>
{cards_html}
    <div style="text-align:center; padding:12px; font-size:12px; color:#999;">
      Weekly Agent &middot; Powered by Claude
    </div>
  </div>
</body>
</html>"""


def main():
    # --date YYMMDD 인자 파싱
    date_short = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--date" and i + 1 < len(args):
            date_short = args[i + 1]

    if not date_short:
        print("Usage: python html_cardnews.py --date YYMMDD")
        sys.exit(1)

    # weekly_analysis_YYYYMMDD.json 찾기
    dt = __import__("datetime").datetime.strptime(date_short, "%y%m%d")
    date_full = dt.strftime("%Y%m%d")
    analysis_path = OUTPUT_DIR / f"weekly_analysis_{date_full}.json"

    if not analysis_path.exists():
        print(f"분석 JSON을 찾을 수 없습니다: {analysis_path}")
        sys.exit(1)

    data = json.loads(analysis_path.read_text(encoding="utf-8"))
    period = data.get("period", {})
    period_start = period.get("start", "??/??")
    period_end = period.get("end", "??/??")

    # MM/DD 형식으로 변환
    try:
        from datetime import datetime as _dt
        ps = _dt.strptime(period_start, "%Y-%m-%d")
        pe = _dt.strptime(period_end, "%Y-%m-%d")
        period_start = ps.strftime("%m/%d")
        period_end = pe.strftime("%m/%d")
    except (ValueError, KeyError):
        pass

    title = f"주간 카드뉴스 ({period_start}~{period_end})"
    categories_data = data.get("categories", {})

    html_content = render_cardnews_html(title, period_start, period_end, categories_data)

    output_path = OUTPUT_DIR / f"WeeklyCardNews_{date_short}.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"카드뉴스 HTML 생성 완료: {output_path}")


if __name__ == "__main__":
    main()
