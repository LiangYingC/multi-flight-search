# multi-flight-search

用 Google Flights 的多段行程搜尋，比較四段票在不同日期與機場組合下的票價，找出最便宜的組合。

每個組合的原始回應會存成一個 JSON 檔，檔名就是快取鍵。查過的組合不會重複呼叫 API，因此可以分批累積資料，之後離線重跑分析。

### 什麼是四段票

一張票包住兩趟不相干的旅行，起點與終點都在國外，中間回台灣進出。

```
第 1 段   亞洲外站 A → 台北       起點在外站，不是台北
第 2 段   台北 → 歐美紐澳目的地
第 3 段   目的地 → 台北
第 4 段   台北 → 亞洲外站 C       頭尾必須同一國家，城市可以不同
```

鐵律是頭與尾必須在同一個國家，城市可以不同。例如大阪 → 台北 → 峇里島 → 台北 → 東京，頭尾都在日本。

之所以便宜，是因為航空公司為了搶香港、泰國、馬來西亞的客源，對這些外站出發的票給轉機優惠價。用中停台北的規則，等於用外國旅客的促銷價買自己的行程。實際案例是台北飛米蘭直飛約 43,000，開成四段票 31,000，省下 12,000。

兩個限制要注意。全票須在第一段起飛後一年內用完，而且不能放棄第一段，no-show 會讓後續航段全部作廢。

`main.py` 的預設設定就是一組四段票，頭尾都在日本，中間是台北進出的紐西蘭來回。

---

## 技術架構

```
FLIGHT_CONFIGS  每段行程的 origins / destinations / dates 清單
      │
      │  generate_combinations() 遞迴展開 Cartesian product
      │  每段各挑一個 origin, destination, date
      ▼
  ┌──────────────────────────────────────────┐
  │  results/<所有航段_日期>_raw.json 已存在?  │
  └──────────────────────────────────────────┘
      │ 是                          │ 否
      ▼                             ▼
   Skip 不呼叫 API              search()
                                    │
                                    ▼
                    SerpApi ─► Google Flights type=3 multi-city
                                    │
                                    ▼
                      results/<所有航段_日期>_raw.json
                                    │
                                    ▼
                                 view.py
                    每個組合取最低價，除以人數換算單人價後排序
```

- **`main.py`** 產生組合、呼叫 API、寫入 JSON
  - `FLIGHT_CONFIGS`：每個航段一個 dict，`origins`、`destinations`、`dates` 都是清單
  - `generate_combinations()`：遞迴走訪所有組合，每個組合送一次查詢
  - `search()`：組出 SerpApi 參數並發出請求，回傳原始 JSON
  - `load_api_key()`：從環境變數或 `.env` 讀取 API key
- **`view.py`** 掃過 `results/*_raw.json`，每個組合取最低價換算成單人價，由低到高排序輸出
- **快取機制** 檔名由所有航段的 `起點_終點_日期` 串成。檔案存在就跳過。查詢失敗時不寫檔，所以下次執行會自動重試
- **零外部依賴** 只使用 Python 標準庫

---

## 使用方式

**1. 取得 API key**

到 <https://serpapi.com/manage-api-key> 註冊並複製 Private API Key。免費方案每月 250 次搜尋。

**2. 寫入 `.env`**

```
SERPAPI_KEY=你的key
```

`.env` 已列入 `.gitignore`，不會進入版本控制。

**3. 編輯 `main.py` 的 `FLIGHT_CONFIGS`**

```python
{
    "origins": ["TPE"],
    "destinations": ["NRT"],
    "dates": ["2026-11-14", "2026-12-12"],
}
```

**4. 執行**

```bash
python3 main.py    # 搜尋並寫入 results/
python3 view.py    # 依價格由低到高列出組合
```

### 注意事項

- 組合數是相乘的。把每段的機場數與日期數全部相乘就是搜尋次數，也就是消耗的額度。新增日期或機場前先算一下總數。
- 多段搜尋要求航段日期遞增，否則 API 回 400。這種失敗不計費。
- 超過約 330 天的日期尚未開賣，查詢會回空結果，而且這種請求會計費。
- 改動 `search()` 裡的搜尋條件之後要手動清掉 `results/`。人數、`stops`、`include_airlines` 都不在檔名裡，快取不會自動失效。
- `search()` 裡有一行註解掉的 `include_airlines`，取消註解即可限定航空公司。

---

## API 資料來源

[SerpApi](https://serpapi.com/google-flights-api) 的 Google Flights API，使用 `type=3` 多段行程搜尋。回傳的每筆 offer 價格涵蓋整趟行程與全部乘客。

免費方案每月 250 次搜尋。失敗的請求不計費，重複送出完全相同的查詢也不計費。
