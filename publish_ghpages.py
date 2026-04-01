"""주간 뉴스레터 HTML 파일을 GitHub Pages(gh-pages 브랜치)에 배포"""

import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from config import WEEKLY_GHPAGES_BASE


# 배포 대상 HTML 파일
HTML_FILES = {
    "WeeklyNewsletter": "주간 뉴스레터",
    "WeeklyCardNews": "주간 카드뉴스",
}

OUTPUT_DIR = Path(__file__).parent / "output"


def get_remote_url():
    """git remote origin URL 반환"""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, cwd=Path(__file__).parent
    )
    return result.stdout.strip()


def publish_to_ghpages(date_short):
    """HTML 파일을 gh-pages 브랜치에 push하고 URL 목록 반환

    Args:
        date_short: YYMMDD 형식 날짜 문자열

    Returns:
        dict: {"date": "YYYY-MM-DD", "urls": {"WeeklyNewsletter": "https://...", ...}}
    """
    # 날짜 파싱
    dt = datetime.strptime(date_short, "%y%m%d")
    date_full = dt.strftime("%Y-%m-%d")
    folder = dt.strftime("%Y/%m/%d")

    # HTML 파일 수집
    found_files = {}
    for prefix in HTML_FILES:
        filename = f"{prefix}_{date_short}.html"
        filepath = OUTPUT_DIR / filename
        if filepath.exists():
            found_files[prefix] = filepath
        else:
            print(f"경고: {filename} 파일 없음, 건너뜀")

    if not found_files:
        print("배포할 HTML 파일이 없습니다.")
        return None

    remote_url = get_remote_url()
    if not remote_url:
        print("git remote origin URL을 찾을 수 없습니다.")
        return None

    tmpdir = tempfile.mkdtemp(prefix="ghpages_weekly_")

    try:
        # gh-pages 브랜치 clone 시도
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", "gh-pages", remote_url, tmpdir],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            # gh-pages 브랜치가 없으면 orphan 브랜치 생성
            print("gh-pages 브랜치가 없습니다. 새로 생성합니다.")
            shutil.rmtree(tmpdir)
            Path(tmpdir).mkdir()
            subprocess.run(["git", "init", tmpdir], capture_output=True, text=True, check=True)
            subprocess.run(
                ["git", "-C", tmpdir, "checkout", "--orphan", "gh-pages"],
                capture_output=True, text=True, check=True
            )
            subprocess.run(
                ["git", "-C", tmpdir, "remote", "add", "origin", remote_url],
                capture_output=True, text=True, check=True
            )

        # tempdir에 git user 설정
        subprocess.run(
            ["git", "-C", tmpdir, "config", "user.name", "Weekly Agent"],
            capture_output=True, text=True
        )
        subprocess.run(
            ["git", "-C", tmpdir, "config", "user.email", "noreply@github.com"],
            capture_output=True, text=True
        )

        # 날짜 폴더 생성
        target_dir = Path(tmpdir) / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        # HTML 파일 복사
        for prefix, filepath in found_files.items():
            shutil.copy2(filepath, target_dir / filepath.name)

        # commit & push
        subprocess.run(["git", "-C", tmpdir, "add", "."], capture_output=True, text=True, check=True)

        # 변경사항 확인
        status = subprocess.run(
            ["git", "-C", tmpdir, "status", "--porcelain"],
            capture_output=True, text=True
        )
        if not status.stdout.strip():
            print("변경사항 없음 (이미 배포된 파일)")
        else:
            subprocess.run(
                ["git", "-C", tmpdir, "commit", "-m", f"Add weekly briefing for {date_full}"],
                capture_output=True, text=True, check=True
            )
            push_result = subprocess.run(
                ["git", "-C", tmpdir, "push", "origin", "gh-pages"],
                capture_output=True, text=True
            )
            if push_result.returncode != 0:
                print(f"push 실패: {push_result.stderr}")
                return None
            print(f"gh-pages 브랜치에 {len(found_files)}개 파일 push 완료")

        # URL 목록 생성
        urls = {}
        for prefix, filepath in found_files.items():
            urls[prefix] = f"{WEEKLY_GHPAGES_BASE}/{folder}/{filepath.name}"

        return {"date": date_full, "urls": urls}

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    # --date 인자 또는 자동 감지 (전날 KST)
    if len(sys.argv) >= 3 and sys.argv[1] == "--date":
        date_short = sys.argv[2]
    else:
        kst_now = datetime.utcnow() + timedelta(hours=9)
        yesterday = kst_now - timedelta(days=1)
        date_short = yesterday.strftime("%y%m%d")

    result = publish_to_ghpages(date_short)

    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
