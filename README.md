# asrock-geo-pipeline

將 ASRock 官網產品規格（Brief）轉換為 Schema.org JSON-LD 結構化資料，
提升產品頁面在 Google AI Overviews、Perplexity、ChatGPT Search 等 AI 搜尋引擎的引用率（GEO）。

---

## 專案背景

官網團隊提供從 CMS 資料庫匯出的 Excel 檔（A 欄：型號、B 欄：Brief HTML）。
本專案以 LLM 將 Brief 改寫為 Schema.org 規範的純文字 `description`，
產出 JSON-LD 檔供工程師嵌入各產品頁 `<head>`，並產出 `preview.html` 供各產線 PM 逐筆檢視內容正確性後再交付。

**作業流程：**
```
官網團隊匯出 Excel → 本專案 LLM 處理 → 人工檢視（preview.html）→ 交付 JSON-LD / 原始 Excel
```

---

## 來源資料

| 檔案 | 工作表 | 產品類別 | 資料筆數 |
|------|--------|----------|----------|
| `AIO.XLSX` | AIO | 一體式水冷散熱器 | 16 |
| `DT.XLSX` | Models | 迷你桌機（Beebox 系列） | 65 |
| `MB.XLSX` | EN | 主機板 | 1,652 |
| `Monitors.xlsx` | Monitors | 顯示器 | 34 |
| `PSU.XLSX` | PSU | 電源供應器 | 48 |
| `VGA.XLSX` | VGA | 顯示卡 | 155 |

- **A 欄（Model）**：產品型號
- **B 欄（Brief）**：產品簡介，部分含 HTML 標籤與 Excel 換行符號（`_x000D_`）

---

## 執行步驟

### 步驟一：產生 Schema.org description（寫入 C 欄）

兩種方式擇一執行：

#### 方式 A：LLM 生成（推薦，GEO 效果更佳）

**腳本**：`generate_schema_description_llm.py`

處理邏輯：
- 使用 Claude API（`claude-haiku-4-5`）將 Brief 轉換為自然語言描述
- 系統提示加入 `cache_control` 降低重複 API 成本
- 每次 API 呼叫批次處理 20 筆，降低請求次數
- 長度控制在 500 字元內，不捏造規格
- 結果寫入每個 Excel 的 **C 欄**，標題為 `description`

API 金鑰請存入 `env.local`（已列入 `.gitignore`，不會進版控）：

```
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
python generate_schema_description_llm.py
```

**預估費用（claude-haiku-4-5，2,370 筆）：** 約 $2–4 USD

#### 方式 B：規則式生成（免費，無需 API 金鑰）

**腳本**：`generate_schema_description.py`

處理邏輯：
- 使用 Python `html.parser` 剝除 B 欄中的 HTML 標籤
- 清理 `_x000D_`（Excel 換行符號）及多餘空白
- 以「型號 + 主要規格」組合成自然語言描述
- 長度控制在 500 字元內，避免 AI 摘要時截斷

```bash
python generate_schema_description.py
```

---

### 步驟二：產生 Schema.org JSON-LD 檔案

**腳本**：`generate_jsonld.py`

處理邏輯：
- 讀取各 Excel 的 A 欄（name）與 C 欄（description）
- 套用 Schema.org `Product` 類型，加入 `brand: ASRock`
- 每個類別輸出一個 `.json` 檔案，內含該類別所有產品的 JSON-LD 陣列

```bash
python generate_jsonld.py
```

**輸出格式：**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "CL-650G",
  "description": "CL-650G. 80 PLUS® GOLD Certified ATX3.1 Ready ...",
  "brand": {
    "@type": "Brand",
    "name": "ASRock"
  }
}
```

---

### 步驟三：建立 HTML 預覽頁面

**腳本**：`build_preview.py`

將 6 個 JSON-LD 檔的所有資料內嵌至單一 HTML 檔案，無需伺服器，直接用瀏覽器開啟即可瀏覽所有產品的結構化資料。

```bash
python build_preview.py
```

---

## 輸出檔案與受眾

| 檔案 | 說明 | 交付對象 |
|------|------|----------|
| `AIO.json` | AIO 水冷 JSON-LD（16 筆） | 網站工程師 |
| `DT.json` | 迷你桌機 JSON-LD（65 筆） | 網站工程師 |
| `MB.json` | 主機板 JSON-LD（1,652 筆） | 網站工程師 |
| `Monitors.json` | 顯示器 JSON-LD（34 筆） | 網站工程師 |
| `PSU.json` | 電源供應器 JSON-LD（48 筆） | 網站工程師 |
| `VGA.json` | 顯示卡 JSON-LD（155 筆） | 網站工程師 |
| `preview.html` | 全產品 JSON-LD 互動預覽頁面 | 各產線 PM 檢視確認 |
| `*.XLSX` / `*.xlsx` | 原始檔，C 欄已新增 `description` | 官網團隊（返還） |

網站工程師將 JSON-LD 嵌入各產品頁的 `<head>`；PM 以 `preview.html` 確認描述內容正確後再交付，維持人工監管環節。

---

## preview.html 使用說明

直接用瀏覽器開啟 `preview.html`，無需安裝任何套件或啟動伺服器。

| 功能 | 說明 |
|------|------|
| **左側分類欄** | 6 個產品類別，點選切換，顯示各類別筆數 |
| **搜尋框** | 即時過濾型號與描述內容 |
| **產品卡片** | 顯示型號、分類標籤、description 預覽 |
| **JSON-LD 按鈕** | 展開 / 收起該產品的完整 JSON-LD 程式碼 |
| **複製按鈕** | 一鍵複製 JSON-LD，可直接貼到網頁 `<script>` 標籤 |
| **分頁導航** | 每頁顯示 24 筆，MB 的 1,652 筆分 69 頁瀏覽 |

### 重新產生

若 Excel 或 JSON 資料更新，依序執行三支腳本即可重建：

```bash
python generate_schema_description_llm.py  # Step 1：更新 Excel C 欄
python generate_jsonld.py                  # Step 2：更新 JSON-LD 檔
python build_preview.py                    # Step 3：重建預覽頁面
```

（API 金鑰從 `env.local` 自動載入，無需手動設定環境變數。）

---

## 網頁嵌入方式

在各產品頁面的 `<head>` 加入對應產品的 JSON-LD：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "CL-650G",
  "description": "CL-650G. 80 PLUS® GOLD Certified ...",
  "brand": {
    "@type": "Brand",
    "name": "ASRock"
  }
}
</script>
```

---

## GEO 效果說明

| 項目 | 說明 |
|------|------|
| 純文字 description | Schema.org 規範要求，AI 可直接讀取 |
| 產品名稱開頭 | AI 引用時語意清晰，易被摘要 |
| 保留關鍵規格數字 | MHz、PLUS®、GDDR6 等術語提升專業可信度 |
| JSON-LD 格式 | Google、Perplexity 等 AI 搜尋引擎優先解析 |

---

## 環境需求

- Python 3.x
- 外部套件詳見 `requirements.txt`

```bash
pip install -r requirements.txt
```

| 套件 | 版本 | 用途 |
|------|------|------|
| `openpyxl` | 3.1.5 | 讀寫 Excel（`.xlsx`） |
| `anthropic` | ≥0.102.0 | Claude API（LLM description 生成） |

其餘使用的 `re`、`json`、`html.parser`、`os` 均為 Python 標準函式庫，無需額外安裝。
