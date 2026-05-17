"""
為 ASRock 產品資料的 Brief (B欄) 生成 Schema.org GEO description，寫入 C 欄。
"""

import re
import openpyxl
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)

    def get_text(self):
        return " ".join(self.parts)


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    stripper = HTMLStripper()
    stripper.feed(str(raw))
    return stripper.get_text()


def clean_text(text: str) -> str:
    # 移除 Excel carriage return artifact
    text = text.replace("_x000D_", " ").replace("\r", " ").replace("\n", " ")
    # 統一空白、移除多餘符號
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*[,;]\s*,", ",", text)
    text = text.strip(" ,;.")
    return text


def build_schema_description(model: str, brief: str) -> str:
    """
    將 model + brief 轉為 Schema.org description：
    - 純文字（無 HTML）
    - 以產品名開頭，列出核心規格
    - GEO 友善：自然語言、易被 AI 引用
    """
    plain = clean_text(strip_html(brief))
    if not plain:
        return model

    # 以句點切分（避免切到小數點：點前後都是數字則不切）
    segments = [s.strip() for s in re.split(r"(?<!\d)\.(?!\d)|[。\n]", plain) if s.strip()]

    # 組合：型號 + 主要規格（最多 3 段，控制在合理長度）
    selected = []
    total_len = len(model) + 2  # "model. "
    for seg in segments:
        if total_len + len(seg) > 500:
            break
        selected.append(seg)
        total_len += len(seg) + 2

    if selected:
        desc = f"{model}. {'. '.join(selected)}."
    else:
        desc = f"{model}. {plain[:497]}."

    return desc


FILES = [
    ("D:/geo/AIO.XLSX",      "AIO"),
    ("D:/geo/DT.XLSX",       "Models"),
    ("D:/geo/MB.XLSX",       "EN"),
    ("D:/geo/Monitors.xlsx", "Monitors"),
    ("D:/geo/PSU.XLSX",      "PSU"),
    ("D:/geo/VGA.XLSX",      "VGA"),
]


def process_file(path: str, sheet_name: str):
    wb = openpyxl.load_workbook(path)
    ws = wb[sheet_name]

    # 確認標題列
    header_a = ws.cell(1, 1).value
    header_b = ws.cell(1, 2).value
    print(f"\n{path}")
    print(f"  A1={header_a!r}  B1={header_b!r}")

    # 寫入 C 欄標題
    ws.cell(1, 3).value = "description"

    processed = 0
    for row in range(2, ws.max_row + 1):
        model = ws.cell(row, 1).value
        brief = ws.cell(row, 2).value
        if model is None and brief is None:
            continue
        desc = build_schema_description(str(model or ""), str(brief or ""))
        ws.cell(row, 3).value = desc
        processed += 1

    wb.save(path)
    print(f"  完成：{processed} 筆 description 已寫入 C 欄")


if __name__ == "__main__":
    for path, sheet in FILES:
        process_file(path, sheet)
    print("\n全部完成！")
