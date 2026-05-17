"""
從 Excel 的 Model (A欄) 與 description (C欄) 產生 Schema.org JSON-LD，
每個產品類別輸出一個 .json 檔案。
"""

import json
import openpyxl

FILES = [
    ("D:/geo/AIO.XLSX",      "AIO",      "D:/geo/AIO.json"),
    ("D:/geo/DT.XLSX",       "Models",   "D:/geo/DT.json"),
    ("D:/geo/MB.XLSX",       "EN",       "D:/geo/MB.json"),
    ("D:/geo/Monitors.xlsx", "Monitors", "D:/geo/Monitors.json"),
    ("D:/geo/PSU.XLSX",      "PSU",      "D:/geo/PSU.json"),
    ("D:/geo/VGA.XLSX",      "VGA",      "D:/geo/VGA.json"),
]


def build_jsonld(model: str, description: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": model,
        "description": description,
        "brand": {
            "@type": "Brand",
            "name": "ASRock"
        }
    }


def process_file(xlsx_path: str, sheet_name: str, out_path: str):
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb[sheet_name]

    # 確認 C1 是 description 欄
    if ws.cell(1, 3).value != "description":
        print(f"  [警告] {xlsx_path} 的 C1 不是 'description'，跳過")
        return

    products = []
    for row in range(2, ws.max_row + 1):
        model = ws.cell(row, 1).value
        desc  = ws.cell(row, 3).value
        if not model and not desc:
            continue
        products.append(build_jsonld(str(model or ""), str(desc or "")))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"  {out_path}  ({len(products)} 筆)")


if __name__ == "__main__":
    print("產生 Schema.org JSON-LD 檔案...")
    for xlsx, sheet, out in FILES:
        process_file(xlsx, sheet, out)
    print("完成！")
