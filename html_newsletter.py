"""주간 뉴스레터 마크다운을 HTML로 변환"""

import sys
import re
import html
from pathlib import Path

from config import CATEGORY_COLORS, CATEGORY_EMOJI

OUTPUT_DIR = Path(__file__).parent / "output"


def md_to_html_body(md_text):
    """간단한 마크다운 → HTML 변환 (뉴스레터 본문용)"""
    lines = md_text.strip().split("\n")
    html_parts = []
    in_paragraph = False

    for line in lines:
        stripped = line.strip()

        # ## 카테고리 헤더
        h2_match = re.match(r"^##\s+(.+)$", stripped)
        if h2_match:
            if in_paragraph:
                html_parts.append("</p>")
                in_paragraph = False
            heading = h2_match.group(1).strip()
            # 카테고리 색상 매칭
            color = "#1a1a2e"
            emoji = ""
            for cat, c in CATEGORY_COLORS.items():
                if cat in heading:
                    color = c
                    emoji = CATEGORY_EMOJI.get(cat, "")
                    break
            heading_html = html.escape(heading)
            html_parts.append(
                f'<div style="margin:28px 0 12px; padding:10px 16px; '
                f'border-left:4px solid {color}; background:{color}0a;">'
                f'<h2 style="margin:0; font-size:18px; color:{color}; line-height:1.4;">'
                f'{emoji} {heading_html}</h2></div>'
            )
            continue

        # ### 소제목
        h3_match = re.match(r"^###\s+(.+)$", stripped)
        if h3_match:
            if in_paragraph:
                html_parts.append("</p>")
                in_paragraph = False
            sub = html.escape(h3_match.group(1).strip())
            html_parts.append(
                f'<h3 style="margin:20px 0 8px; font-size:15px; color:#333; '
                f'font-weight:600; line-height:1.4;">{sub}</h3>'
            )
            continue

        # 빈 줄 = 문단 분리
        if not stripped:
            if in_paragraph:
                html_parts.append("</p>")
                in_paragraph = False
            continue

        # **볼드** 처리
        processed = html.escape(stripped)
        processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", processed)

        # 일반 텍스트 → 문단
        if not in_paragraph:
            html_parts.append(
                '<p style="margin:0 0 8px; font-size:14px; color:#333; line-height:1.75;">'
            )
            in_paragraph = True
            html_parts.append(processed)
        else:
            html_parts.append("<br>" + processed)

    if in_paragraph:
        html_parts.append("</p>")

    return "\n".join(html_parts)


def render_newsletter_html(title, period_start, period_end, md_content):
    """주간 뉴스레터 전체 HTML 렌더링"""
    body_html = md_to_html_body(md_content)
    title_html = html.escape(title)
    period_str = f"{period_start} ~ {period_end}"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_html}</title>
</head>
<body style="margin:0; padding:16px; background:#f5f5f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;">
  <div style="max-width:640px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color:#fff; padding:24px;">
      <h1 style="margin:0; font-size:22px; font-weight:700;">&#128202; {title_html}</h1>
      <p style="margin:8px 0 0; font-size:14px; color:rgba(255,255,255,0.7);">{html.escape(period_str)}</p>
    </div>
    <div style="padding:8px 24px 24px;">
{body_html}
    </div>
    <div style="padding:12px 24px; text-align:center; font-size:12px; color:#999; border-top:1px solid #eee;">
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
        print("Usage: python html_newsletter.py --date YYMMDD")
        sys.exit(1)

    # weekly_newsletter_YYYYMMDD.md 찾기
    dt = __import__("datetime").datetime.strptime(date_short, "%y%m%d")
    date_full = dt.strftime("%Y%m%d")
    md_path = OUTPUT_DIR / f"weekly_newsletter_{date_full}.md"

    if not md_path.exists():
        print(f"마크다운 파일을 찾을 수 없습니다: {md_path}")
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")

    # 기간 정보 추출 (첫 줄이나 메타데이터에서)
    period_match = re.search(r"(\d{2}/\d{2})\s*~\s*(\d{2}/\d{2})", md_text)
    if period_match:
        period_start = period_match.group(1)
        period_end = period_match.group(2)
    else:
        period_start = "??/??"
        period_end = "??/??"

    # 제목 추출 (첫 번째 # 헤더)
    title_match = re.match(r"^#\s+(.+)$", md_text.strip(), re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"주간 브리핑 ({date_short})"

    # # 헤더 라인 제거 (본문에서)
    body = re.sub(r"^#\s+.+$", "", md_text, count=1, flags=re.MULTILINE).strip()

    html_content = render_newsletter_html(title, period_start, period_end, body)

    output_path = OUTPUT_DIR / f"WeeklyNewsletter_{date_short}.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"주간 뉴스레터 HTML 생성 완료: {output_path}")


if __name__ == "__main__":
    main()
