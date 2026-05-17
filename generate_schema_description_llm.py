"""
使用 Claude API (LLM) 為 ASRock 產品的 Brief 重新生成 GEO 友善的 Schema.org description，
結果寫回各 Excel 的 C 欄。

用法：
  set ANTHROPIC_API_KEY=sk-ant-...
  python generate_schema_description_llm.py
"""

import json
import os
import re
import time
import openpyxl
import anthropic
from html.parser import HTMLParser

# ── 設定 ──────────────────────────────────────────────────────────────────────
MODEL      = "claude-haiku-4-5"
BATCH_SIZE = 20          # 每次 API 呼叫的產品數量
MAX_RETRY  = 3           # 最多重試次數

FILES = [
    ("D:/geo/AIO.XLSX",      "AIO"),
    ("D:/geo/DT.XLSX",       "Models"),
    ("D:/geo/MB.XLSX",       "EN"),
    ("D:/geo/Monitors.xlsx", "Monitors"),
    ("D:/geo/PSU.XLSX",      "PSU"),
    ("D:/geo/VGA.XLSX",      "VGA"),
]

SYSTEM_PROMPT = """\
You are a technical copywriter for ASRock, a hardware manufacturer.
Your task: given a product model name and a raw HTML/text brief, write a clean, \
GEO-optimized (Generative Engine Optimization) Schema.org "description" string.

Rules:
1. Plain text only — NO HTML tags, NO markdown.
2. Start with the model name, followed by a period and a space.
3. Highlight the most important specs: wattage, efficiency rating, socket/platform, \
   chipset, GPU chip, memory type/speed, display size/resolution, cooling type, etc.
4. Write in natural English sentences, readable by both humans and AI search engines.
5. Max 500 characters total (including model name). If brief is short, preserve all info.
6. Do NOT invent specs not present in the brief.
7. Remove filler phrases like "please refer to", "for details", "subject to change".
"""

# ── HTML 清理 ─────────────────────────────────────────────────────────────────
class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        s = data.strip()
        if s:
            self.parts.append(s)

    def get_text(self):
        return " ".join(self.parts)


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    p = HTMLStripper()
    p.feed(str(raw))
    return p.get_text()


def clean_brief(brief: str) -> str:
    text = strip_html(brief)
    text = text.replace("_x000D_", " ").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ── LLM 呼叫 ─────────────────────────────────────────────────────────────────
def call_llm(client: anthropic.Anthropic, batch: list[dict]) -> list[str]:
    """
    傳入 [{"model": ..., "brief": ...}, ...] 陣列，
    回傳同長度的 description 字串陣列。
    """
    user_content = json.dumps(batch, ensure_ascii=False)

    for attempt in range(1, MAX_RETRY + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Generate a Schema.org description for each product below.\n"
                            "Return ONLY a JSON array of strings (same order, same count).\n\n"
                            + user_content
                        ),
                    }
                ],
            )

            raw = response.content[0].text.strip()

            # 擷取 JSON 陣列（忽略前後可能的文字）
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if not m:
                raise ValueError(f"No JSON array found in response:\n{raw[:300]}")

            result = json.loads(m.group())
            if not isinstance(result, list) or len(result) != len(batch):
                raise ValueError(
                    f"Expected {len(batch)} items, got {len(result)}"
                )
            return result

        except Exception as e:
            if attempt < MAX_RETRY:
                wait = 2 ** attempt
                print(f"    [retry {attempt}/{MAX_RETRY}] {e}  (wait {wait}s)")
                time.sleep(wait)
            else:
                print(f"    [failed] {e}")
                # 回退：直接用清理後的 brief
                return [f"{item['model']}. {item['brief'][:490]}." for item in batch]


# ── 處理單一 Excel ────────────────────────────────────────────────────────────
def process_file(client: anthropic.Anthropic, path: str, sheet_name: str):
    print(f"\n{path}")
    wb = openpyxl.load_workbook(path)
    ws = wb[sheet_name]

    # 確認標題列
    ws.cell(1, 3).value = "description"

    # 收集所有列
    rows = []
    for row in range(2, ws.max_row + 1):
        model = ws.cell(row, 1).value
        brief = ws.cell(row, 2).value
        if model is None and brief is None:
            continue
        rows.append((row, str(model or ""), clean_brief(str(brief or ""))))

    total   = len(rows)
    batches = [rows[i : i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    done    = 0

    for batch in batches:
        payload = [{"model": m, "brief": b} for _, m, b in batch]
        descriptions = call_llm(client, payload)

        for (row_idx, _, _), desc in zip(batch, descriptions):
            ws.cell(row_idx, 3).value = desc

        done += len(batch)
        print(f"  {done}/{total}", end="\r", flush=True)

    wb.save(path)
    print(f"  完成：{total} 筆 description 已寫入 C 欄          ")


# ── 主程式 ────────────────────────────────────────────────────────────────────
def load_env_local(path: str = "D:/geo/env.local") -> None:
    """從 env.local 載入 KEY=VALUE 至 os.environ（不覆蓋已存在的值）。"""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    load_env_local()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "錯誤：找不到 ANTHROPIC_API_KEY\n"
            "  請在 D:/geo/env.local 加入：ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)

    for path, sheet in FILES:
        process_file(client, path, sheet)

    print("\n全部完成！接著執行：")
    print("  python generate_jsonld.py")
    print("  python build_preview.py")
