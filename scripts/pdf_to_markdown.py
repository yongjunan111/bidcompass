"""
PDF → Markdown 변환기
사용법: python pdf_to_markdown.py <input.pdf> [output.md]

설치: pip install pdfplumber
"""

import sys
import re
import pdfplumber


def table_to_markdown(table: list) -> str:
    """2D 리스트 테이블을 Markdown 테이블로 변환"""
    if not table or not table[0]:
        return ""

    cleaned = [
        [str(cell).strip() if cell is not None else "" for cell in row]
        for row in table
    ]

    header = cleaned[0]
    rows = cleaned[1:]

    md = "| " + " | ".join(header) + " |\n"
    md += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in rows:
        while len(row) < len(header):
            row.append("")
        md += "| " + " | ".join(row[: len(header)]) + " |\n"

    return md


def is_in_any_bbox(word, bboxes, tolerance=2):
    """단어가 주어진 bounding box 목록 중 하나에 포함되는지 확인"""
    wx0 = word["x0"]
    wtop = word["top"]
    wx1 = word["x1"]
    wbottom = word["bottom"]

    for tb in bboxes:
        if (
            wx0 >= tb[0] - tolerance
            and wtop >= tb[1] - tolerance
            and wx1 <= tb[2] + tolerance
            and wbottom <= tb[3] + tolerance
        ):
            return True
    return False


def classify_heading(text: str, font_size: float, avg_size: float, max_size: float) -> str:
    """폰트 크기 기반 헤딩 레벨 결정"""
    if font_size >= max_size * 0.95:
        return f"# {text}"
    elif font_size >= avg_size * 1.3:
        return f"## {text}"
    elif font_size >= avg_size * 1.1:
        return f"### {text}"
    return text


def group_words_into_lines(words, y_tolerance=3):
    """단어들을 y좌표 기준으로 라인 단위로 그룹화"""
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    lines = []
    current_line = [sorted_words[0]]

    for word in sorted_words[1:]:
        if abs(word["top"] - current_line[0]["top"]) <= y_tolerance:
            current_line.append(word)
        else:
            current_line.sort(key=lambda w: w["x0"])
            lines.append(current_line)
            current_line = [word]

    if current_line:
        current_line.sort(key=lambda w: w["x0"])
        lines.append(current_line)

    return lines


def pdf_to_markdown(pdf_path: str) -> str:
    md_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            md_lines.append(f"\n---\n<!-- Page {page_num} -->\n")

            # 테이블 추출 및 bounding box 수집
            found_tables = page.find_tables()
            tables = [t.extract() for t in found_tables]
            table_bboxes = [t.bbox for t in found_tables]

            # 단어별 폰트 정보 포함 추출
            all_words = page.extract_words(extra_attrs=["size", "fontname"])

            # 테이블 영역에 속하지 않는 단어만 필터링
            text_words = [w for w in all_words if not is_in_any_bbox(w, table_bboxes)]

            # 전체 페이지의 폰트 크기 통계 (헤딩 감지용)
            all_sizes = [w["size"] for w in all_words if w.get("size")]
            avg_size = sum(all_sizes) / len(all_sizes) if all_sizes else 0
            max_size = max(all_sizes) if all_sizes else 0

            # 테이블 영역을 y좌표 기준 정렬을 위해 수집
            # (테이블과 텍스트를 문서 순서대로 배치)
            elements = []  # (y_position, type, content)

            # 텍스트 라인 그룹화
            lines = group_words_into_lines(text_words)
            for line_words in lines:
                y_pos = line_words[0]["top"]
                text = " ".join(w["text"] for w in line_words)
                line_avg_size = (
                    sum(w["size"] for w in line_words if w.get("size")) / len(line_words)
                    if line_words
                    else 0
                )
                elements.append((y_pos, "text", text, line_avg_size))

            # 테이블을 y좌표와 함께 추가
            for i, table in enumerate(tables):
                y_pos = table_bboxes[i][1]  # 테이블 상단 y좌표
                elements.append((y_pos, "table", table, 0))

            # y좌표 기준 정렬하여 문서 순서 유지
            elements.sort(key=lambda e: e[0])

            prev_was_empty = False
            for elem in elements:
                if elem[1] == "text":
                    text = elem[2]
                    line_avg_size = elem[3]
                    stripped = text.strip()

                    if not stripped:
                        if not prev_was_empty:
                            md_lines.append("")
                            prev_was_empty = True
                        continue

                    prev_was_empty = False

                    # 짧은 라인 + 큰 폰트 → 헤딩 후보
                    if line_avg_size > 0 and len(stripped) < 80 and avg_size > 0:
                        line_md = classify_heading(stripped, line_avg_size, avg_size, max_size)
                    else:
                        line_md = stripped

                    md_lines.append(line_md)

                elif elem[1] == "table":
                    prev_was_empty = False
                    table_md = table_to_markdown(elem[2])
                    if table_md:
                        md_lines.append("\n" + table_md)

    result = "\n".join(md_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def main():
    if len(sys.argv) < 2:
        print("사용법: python pdf_to_markdown.py <input.pdf> [output.md]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.replace(".pdf", ".md")

    print(f"변환 중: {pdf_path} → {output_path}")

    markdown = pdf_to_markdown(pdf_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"완료! 저장됨: {output_path}")
    print(f"총 {len(markdown.splitlines())}줄 생성")


if __name__ == "__main__":
    main()
