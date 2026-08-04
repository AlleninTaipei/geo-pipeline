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

## Q & A：單一 HTML + 前端 i18n 架構下的 SEO 與 GEO 考量

### Q1：單一 HTML + 前端 i18n 這種做法, 要怎樣顧及 SEO 或 GEO ?

單一 HTML 加前端 i18n 的做法, 對 SEO 跟 GEO 有一個共同的根本問題,
原始 HTML 在還沒執行 JS 前幾乎沒有可讀文字, 正文內容都是靠 JS 執行時填進去的,
爬蟲拿到的原始檔案內容很單薄.

SEO 跟 GEO 對這件事的敏感度不同, 分開來看:

SEO 方面, Google 的爬蟲會執行 JS 渲染, 理論上仍能看到 JS 填完字之後的內容,
但渲染需要排隊, 通常比純靜態頁面晚幾天到幾週才會被索引,
且不是所有搜尋引擎都完整支援 JS 渲染. 另外若語言切換只靠同一個 URL 加
localStorage 記住語言, 沒有給每個語言版本各自獨立的網址,
就無法用 hreflang 標籤告訴搜尋引擎這是同一頁的不同語言版本,
各語言版本也無法被各自獨立索引.

GEO 方面問題更直接. 目前主流的生成式引擎爬蟲, 例如 GPTBot, ClaudeBot,
Google-Extended, PerplexityBot, 幾乎都只抓原始 HTML 文字, 不執行 JavaScript.
對這些爬蟲來說, 只靠 JS 填字的頁面幾乎是一片空白, 沒有內容可以被引用或摘要進生成式答案裡.
這不是排名會不會被拖慢的問題, 而是幾乎完全不可見.

若想保留單一 HTML 加前端 i18n 這種好維護的架構, 同時解決這個問題,
具體做法通常是:

1. 加一個輕量的建置步驟, 讀取同一份語系資料, 產出每個語言各自的靜態 HTML,
   把翻譯好的文字直接寫進標籤裡, 而不是留空等 JS 填. 前端程式之後照樣接手處理互動與語言切換,
   維護時仍然只改一份語系資料檔, 但爬蟲拿到的就是真正有內容的 HTML.
2. 每個語言版本各自的頁面互相加上 hreflang 與各自的 canonical 標籤.
3. 在靜態 HTML 裡直接內嵌 schema.org 結構化資料 (Organization, Product, FAQPage),
   這對 GEO 特別重要, 生成式引擎偏好可以直接摘錄的結構化事實.
4. `<html lang="...">` 要跟著各語言版本靜態決定, 不能只靠 JS 執行後才設定.

若堅持零建置步驟, SEO 與 GEO 的改善空間會很有限,
頂多只能做到 hreflang 與結構化資料這兩項不需要建置就能加的部分.

### Q2："內嵌 schema.org" 也有多語系要維護嗎 ?

要看放的是哪些欄位, 整體結論是: 有文字內容的欄位要跟著多語系維護, 純結構性欄位不用.

JSON-LD 區塊裡, 像 Organization 的 name, description, Product 的 name, description,
FAQPage 的每一個 question 與 answer, 這些都是給人看也給引擎讀的文字內容,
必須跟頁面實際顯示的語言一致, 否則會出現結構化資料跟畫面文字語言不符的問題.
這也牽涉到 Google 的搜尋品質規範, 結構化資料必須忠實反映頁面實際內容,
語言不一致可能導致該筆結構化資料被忽略甚至被視為濫用信號.

不需要跟著語言變動的欄位是像 url, sameAs, logo, image, telephone, email,
這些本身是純資料不是自然語言, 不用翻譯.

這不算額外的翻譯工作量, 因為 JSON-LD 裡要填的文字, 本質上就是語系資料檔裡已經存在的同一份資料
(公司名稱, 產品說明, 服務描述), 只是換一種包裝格式輸出.

但這裡有一個限制: 若 JSON-LD 是用 JS 動態寫進頁面的, 對不執行 JS 的 GEO 爬蟲來說一樣不可見,
跟畫面上其他 JS 填字的內容有一樣的可見度問題, 並沒有繞過 Q1 提到的根本限制.
若要讓結構化資料真正對這些爬蟲可見, 仍須靠建置步驟, 在產出每個語言各自的靜態 HTML 時,
把對應語言的 JSON-LD 也一起寫進那份 HTML 裡, 維護上依然是同一份語系資料當唯一資料來源,
只是輸出產物需要跟正文一樣, 每個語言各自一份靜態內容.

### Q3：geo-pipeline 這個專案跟上述概念的對應關係是什麼 ?

geo-pipeline 是上述概念的一個具體實作案例, 已經是 ASRock 內部實際在跑的流程,
用來解決硬體產品頁的 GEO 問題.

流程是 Excel (型號加 Brief HTML) 進, LLM (`claude-haiku-4-5`) 把雜訊 HTML
改寫成乾淨的自然語言 description, 寫回 Excel C 欄, 再組成 Schema.org Product JSON-LD,
每個產品類別各輸出一個 `.json` 檔, 最後產生 `preview.html` 讓各產線 PM 逐筆人工檢視內容是否正確,
確認後才交給網站工程師手動貼進各產品頁 `<head>`.

這正好對應 Q1 與 Q2 的建議方向, 把結構化資料的產生從執行期 (JS 動態寫入)
移到建置期 (離線批次產生靜態 JSON-LD 檔), 再由人工把靜態內容嵌進頁面,
確保 GEO 爬蟲不執行 JS 也能讀到.

值得注意的落差: `generate_schema_description_llm.py` 的 SYSTEM_PROMPT 目前明確寫死
"Write in natural English sentences", 整條 pipeline 目前完全是單語言 (英文),
沒有任何 zh-TW 或其他語言的分支或參數. 對應 Q2 的結論, description 這類文字欄位理論上要跟著語言版本走,
但目前這條 pipeline 還沒做到, 產出的 JSON-LD 只服務英文頁面.
若對應的中文產品頁也想要有結構化資料, 目前這個工具鏈覆蓋不到, 這是已知缺口, 而非設計選擇.

### 會議陳述參考：五個可獨立討論的觀念

1. chatbot 上線跟前端多語言架構重構是兩個獨立決策, 不互相依賴, 不需要互相等待.
2. 單一 HTML 加前端 i18n 跟多份各自獨立頁面的取捨, 是維護成本跟爬蟲可見度的權衡, 不是誰對誰錯.
3. SEO 跟 GEO 對 JS 執行的容忍度不一樣. Google 會執行 JS 但排隊渲染會拖慢索引,
   GPTBot, ClaudeBot, Google-Extended, PerplexityBot 等生成式引擎爬蟲幾乎都只讀原始 HTML,
   不是排名較差, 而是完全不可見.
4. Schema.org 結構化資料裡的文字欄位必須跟隨頁面實際顯示的語言, 這是 Google 結構化資料規範的要求,
   不是可以脫鉤處理的細節.
5. geo-pipeline 已經是 建置期產生靜態結構化資料, 人工審核, 再嵌入 這套流程在公司內部可行且已經在跑的證明,
   但目前只覆蓋英文, 擴充多語言是後續要另外規劃的工作項目, 不是現有 pipeline 已經具備的能力.

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
