"""5일치 Daily 뉴스레터 HTML을 GitHub Pages에서 가져와 통합 JSON으로 변환"""

import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser

import requests

from config import (
    NEWS_GHPAGES_BASE, BLOG_GHPAGES_BASE, YOUTUBE_GHPAGES_BASE,
    NEWS_FILES, HEADERS, FETCH_DAYS, MIN_DAYS_REQUIRED,
)

OUTPUT_DIR = Path(__file__).parent / "output"


# ──────────────────────────────────────────
# HTML 파서: News / TheBell
# ──────────────────────────────────────────

class NewsHTMLParser(HTMLParser):
    """Daily News Agent가 생성한 HTML에서 기사 목록 추출.

    구조: <div> 안에 <h2>번호. 제목</h2> <p>요약</p> <a href="링크">
    """

    def __init__(self):
        super().__init__()
        self.articles = []
        self._current = None
        self._tag_stack = []
        self._capture = None  # "title" | "summary" | None

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        attrs_dict = dict(attrs)

        if tag == "h2":
            self._current = {"title": "", "summary": "", "link": ""}
            self._capture = "title"
        elif tag == "p" and self._current is not None:
            style = attrs_dict.get("style", "")
            # 기자명(12px color:#888) 은 요약에 포함
            if "color:#444" in style or "color:#888" in style:
                self._capture = "summary"
        elif tag == "a" and self._current is not None:
            href = attrs_dict.get("href", "")
            if href and href.startswith("http"):
                self._current["link"] = href

    def handle_endtag(self, tag):
        if self._tag_stack:
            self._tag_stack.pop()
        if tag == "h2":
            self._capture = None
        elif tag == "p":
            self._capture = None
        elif tag == "div" and self._current and self._current["title"]:
            self.articles.append(self._current)
            self._current = None

    def handle_data(self, data):
        if self._capture == "title" and self._current is not None:
            self._current["title"] += data
        elif self._capture == "summary" and self._current is not None:
            text = data.strip()
            if text:
                if self._current["summary"]:
                    self._current["summary"] += " " + text
                else:
                    self._current["summary"] = text

    def handle_entityref(self, name):
        pass

    def handle_charref(self, name):
        pass


def parse_news_html(html_text):
    """News/TheBell HTML → [{"title", "summary", "link"}]"""
    parser = NewsHTMLParser()
    parser.feed(html_text)
    results = []
    for art in parser.articles:
        # 번호 접두사 제거: "1. 제목" → "제목"
        title = re.sub(r"^\d+\.\s*", "", art["title"]).strip()
        if title:
            results.append({
                "title": title,
                "summary": art["summary"].strip(),
                "link": art["link"],
            })
    return results


# ──────────────────────────────────────────
# HTML 파서: Blog
# ──────────────────────────────────────────

class BlogHTMLParser(HTMLParser):
    """Daily Blog Agent HTML에서 블로그 글 목록 추출.

    구조: <h3>번호. 제목</h3> <p>요약</p> <a href="링크">
    Blog별 섹션: <div style="border-left: 3px solid #2ecc71"> <h3>블로그명</h3>
    """

    def __init__(self):
        super().__init__()
        self.articles = []
        self._current = None
        self._current_blog = ""
        self._capture = None  # "blog_name" | "title" | "summary"
        self._in_blog_header = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        style = attrs_dict.get("style", "")

        # 블로그 섹션 헤더 감지
        if tag == "div" and "border-left" in style and "#2ecc71" in style:
            self._in_blog_header = True
        elif tag == "h3" and self._in_blog_header:
            self._capture = "blog_name"
            self._current_blog = ""
        elif tag == "h3" and not self._in_blog_header:
            # 개별 기사 제목
            self._current = {"title": "", "summary": "", "link": "", "blog": self._current_blog}
            self._capture = "title"
        elif tag == "p" and self._current is not None:
            if "color:#444" in style or "color:#555" in style:
                self._capture = "summary"
        elif tag == "a" and self._current is not None:
            href = attrs_dict.get("href", "")
            if href and href.startswith("http"):
                self._current["link"] = href

    def handle_endtag(self, tag):
        if tag == "h3":
            if self._capture == "blog_name":
                self._in_blog_header = False
            self._capture = None
        elif tag == "p":
            self._capture = None
        elif tag == "div" and self._current and self._current["title"]:
            self.articles.append(self._current)
            self._current = None

    def handle_data(self, data):
        if self._capture == "blog_name":
            self._current_blog += data
        elif self._capture == "title" and self._current is not None:
            self._current["title"] += data
        elif self._capture == "summary" and self._current is not None:
            text = data.strip()
            if text:
                if self._current["summary"]:
                    self._current["summary"] += " " + text
                else:
                    self._current["summary"] = text


def parse_blog_html(html_text):
    """Blog HTML → [{"title", "summary", "link", "blog"}]"""
    parser = BlogHTMLParser()
    parser.feed(html_text)
    results = []
    for art in parser.articles:
        title = re.sub(r"^\d+\.\s*", "", art["title"]).strip()
        if title:
            results.append({
                "title": title,
                "summary": art["summary"].strip(),
                "link": art["link"],
                "blog": art.get("blog", "").strip(),
            })
    return results


# ──────────────────────────────────────────
# HTML 파서: YouTube
# ──────────────────────────────────────────

class YouTubeHTMLParser(HTMLParser):
    """Daily YouTube Agent HTML에서 영상 요약 추출.

    구조: <h2>번호. 제목</h2> <p>채널명</p>
    4분류: 핵심 주장 / 근거 및 논리 / 팩트 / 의견
    키워드, 영상 링크
    """

    def __init__(self):
        super().__init__()
        self.articles = []
        self._current = None
        self._capture = None  # "title" | "channel" | "section" | "keywords"
        self._section_label = ""
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        attrs_dict = dict(attrs)
        style = attrs_dict.get("style", "")

        if tag == "h2":
            self._current = {
                "title": "", "channel": "", "link": "",
                "core_claim": "", "evidence": "", "facts": "", "opinion": "",
                "keywords": "",
            }
            self._capture = "title"
        elif tag == "p" and self._current is not None:
            if "color:#888" in style and "12px" in style and not self._current["channel"]:
                self._capture = "channel"
            elif "font-weight:bold" in style and "color:#1a1a2e" in style:
                self._capture = "section_label"
                self._section_label = ""
            elif "color:#444" in style and "14px" in style:
                self._capture = "section_value"
            elif "color:#6b7280" in style:
                self._capture = "keywords"
        elif tag == "a" and self._current is not None:
            href = attrs_dict.get("href", "")
            if href and "youtube.com" in href:
                self._current["link"] = href

    def handle_endtag(self, tag):
        if self._tag_stack:
            self._tag_stack.pop()
        if tag == "h2":
            self._capture = None
        elif tag == "p":
            self._capture = None
        elif tag == "div" and self._current and self._current["title"]:
            self.articles.append(self._current)
            self._current = None

    def handle_data(self, data):
        if self._current is None:
            return

        if self._capture == "title":
            self._current["title"] += data
        elif self._capture == "channel":
            self._current["channel"] += data
        elif self._capture == "section_label":
            self._section_label += data
        elif self._capture == "section_value":
            text = data.strip()
            if not text:
                return
            label = self._section_label
            if "핵심 주장" in label:
                self._current["core_claim"] += (" " + text if self._current["core_claim"] else text)
            elif "근거" in label:
                self._current["evidence"] += (" " + text if self._current["evidence"] else text)
            elif "팩트" in label:
                self._current["facts"] += (" " + text if self._current["facts"] else text)
            elif "의견" in label:
                self._current["opinion"] += (" " + text if self._current["opinion"] else text)
        elif self._capture == "keywords":
            self._current["keywords"] += data


def parse_youtube_html(html_text):
    """YouTube HTML → [{"title", "channel", "link", "core_claim", "evidence", "facts", "opinion", "keywords"}]"""
    parser = YouTubeHTMLParser()
    parser.feed(html_text)
    results = []
    for art in parser.articles:
        title = re.sub(r"^\d+\.\s*", "", art["title"]).strip()
        if title:
            kw_text = art.get("keywords", "")
            kw_text = re.sub(r"^.*키워드:\s*", "", kw_text)
            keywords = [k.strip() for k in kw_text.split(",") if k.strip()]
            results.append({
                "title": title,
                "channel": art["channel"].strip(),
                "link": art["link"],
                "core_claim": art["core_claim"].strip(),
                "evidence": art["evidence"].strip(),
                "facts": art["facts"].strip(),
                "opinion": art["opinion"].strip(),
                "keywords": keywords,
            })
    return results


# ──────────────────────────────────────────
# 데이터 수집 메인 로직
# ──────────────────────────────────────────

def fetch_url(url):
    """URL에서 HTML 텍스트를 가져옴. 실패 시 None 반환."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.text
        return None
    except requests.RequestException:
        return None


def category_from_filename(filename):
    """파일명 접두사에서 원본 카테고리명 추출"""
    mapping = {
        "NaverNews_macro": "매크로",
        "NaverNews_ma": "M&A",
        "NaverNews_pe": "PE",
        "NaverNews_vc": "VC",
        "NaverNews_stock": "주식",
        "TheBell_deal": "더벨_Deal",
        "TheBell_finance": "더벨_금융",
        "TheBell_invest": "더벨_투자",
        "TheBell_industry": "더벨_산업",
    }
    return mapping.get(filename, filename)


def determine_date_range(end_date=None):
    """수집 대상 날짜 범위(5일) 결정. end_date가 None이면 어제(KST) 기준."""
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        kst_now = datetime.utcnow() + timedelta(hours=9)
        end_dt = kst_now - timedelta(days=1)

    dates = []
    dt = end_dt
    while len(dates) < FETCH_DAYS:
        dates.append(dt)
        dt -= timedelta(days=1)

    dates.reverse()
    return dates


def fetch_all(dates):
    """모든 소스에서 데이터 수집"""
    all_items = []
    fetched_dates = set()

    for dt in dates:
        date_str = dt.strftime("%Y-%m-%d")
        date_short = dt.strftime("%y%m%d")
        folder = dt.strftime("%Y/%m/%d")
        day_has_data = False

        # News (9 files)
        for prefix in NEWS_FILES:
            filename = f"{prefix}_{date_short}.html"
            url = f"{NEWS_GHPAGES_BASE}/{folder}/{filename}"
            html_text = fetch_url(url)
            if html_text:
                articles = parse_news_html(html_text)
                for art in articles:
                    all_items.append({
                        "date": date_str,
                        "source": "news",
                        "category_original": category_from_filename(prefix),
                        "title": art["title"],
                        "summary": art["summary"],
                        "link": art["link"],
                    })
                day_has_data = True
                print(f"  [News] {date_str} {prefix}: {len(articles)}건")

        # Blog (1 file)
        blog_url = f"{BLOG_GHPAGES_BASE}/{folder}/NaverBlog_{date_short}.html"
        html_text = fetch_url(blog_url)
        if html_text:
            articles = parse_blog_html(html_text)
            for art in articles:
                all_items.append({
                    "date": date_str,
                    "source": "blog",
                    "category_original": f"블로그_{art.get('blog', '')}",
                    "title": art["title"],
                    "summary": art["summary"],
                    "link": art["link"],
                })
            day_has_data = True
            print(f"  [Blog] {date_str}: {len(articles)}건")

        # YouTube (1 file)
        yt_url = f"{YOUTUBE_GHPAGES_BASE}/{folder}/newsletter_{date_str}.html"
        html_text = fetch_url(yt_url)
        if html_text:
            articles = parse_youtube_html(html_text)
            for art in articles:
                summary_parts = []
                if art["core_claim"]:
                    summary_parts.append(f"[핵심] {art['core_claim']}")
                if art["evidence"]:
                    summary_parts.append(f"[근거] {art['evidence']}")
                if art["facts"]:
                    summary_parts.append(f"[팩트] {art['facts']}")
                if art["opinion"]:
                    summary_parts.append(f"[의견] {art['opinion']}")
                combined_summary = " ".join(summary_parts)
                keywords_str = ", ".join(art.get("keywords", []))

                all_items.append({
                    "date": date_str,
                    "source": "youtube",
                    "category_original": f"유튜브_{art.get('channel', '')}",
                    "title": art["title"],
                    "summary": combined_summary,
                    "link": art["link"],
                    "keywords": keywords_str,
                })
            day_has_data = True
            print(f"  [YouTube] {date_str}: {len(articles)}건")

        if day_has_data:
            fetched_dates.add(date_str)

    return all_items, sorted(fetched_dates)


def main():
    # --end-date 인자 파싱
    end_date = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--end-date" and i + 1 < len(args):
            end_date = args[i + 1]

    print("=== Weekly Agent: 데이터 수집 시작 ===")
    dates = determine_date_range(end_date)
    print(f"수집 기간: {dates[0].strftime('%Y-%m-%d')} ~ {dates[-1].strftime('%Y-%m-%d')}")

    items, fetched_dates = fetch_all(dates)

    if len(fetched_dates) < MIN_DAYS_REQUIRED:
        print(f"\n⚠️ 수집된 날짜({len(fetched_dates)}일)가 최소 요구({MIN_DAYS_REQUIRED}일) 미만입니다.")
        sys.exit(1)

    # 결과 저장
    OUTPUT_DIR.mkdir(exist_ok=True)
    end_dt = dates[-1]
    output_filename = f"weekly_raw_{end_dt.strftime('%Y%m%d')}.json"
    output_path = OUTPUT_DIR / output_filename

    result = {
        "period": {
            "start": dates[0].strftime("%Y-%m-%d"),
            "end": dates[-1].strftime("%Y-%m-%d"),
        },
        "fetched_dates": fetched_dates,
        "total_items": len(items),
        "source_counts": {
            "news": sum(1 for x in items if x["source"] == "news"),
            "blog": sum(1 for x in items if x["source"] == "blog"),
            "youtube": sum(1 for x in items if x["source"] == "youtube"),
        },
        "items": items,
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 수집 완료: {output_path}")
    print(f"   기간: {result['period']['start']} ~ {result['period']['end']}")
    print(f"   수집 날짜: {len(fetched_dates)}일 ({', '.join(fetched_dates)})")
    print(f"   총 {len(items)}건 (뉴스 {result['source_counts']['news']} / "
          f"블로그 {result['source_counts']['blog']} / "
          f"유튜브 {result['source_counts']['youtube']})")


if __name__ == "__main__":
    main()
