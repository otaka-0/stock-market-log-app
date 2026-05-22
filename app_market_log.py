from datetime import date

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# ==================================================
# 基本設定
# ==================================================

st.set_page_config(
    page_title="株研究 相場観察アプリ",
    layout="wide"
)

st.title("株研究 相場観察アプリ")
st.caption("選択式で相場観察を記録し、Googleスプレッドシートに保存します。")


# ==================================================
# Google Sheets 接続設定
# ==================================================

SHEET_NAME = "market_logs"

HEADERS = [
    "date",
    "nikkei_direction",
    "nikkei_strength",
    "nikkei_ma",
    "nikkei_memo",
    "growth_strength",
    "growth_vs_nikkei",
    "small_stock_flow",
    "growth_memo",
    "themes",
    "theme_memo",
    "code",
    "stock_name",
    "reason",
    "chart_features",
    "stock_memo",
    "today_learning",
    "tomorrow_watch",
]


@st.cache_resource
def get_worksheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    spreadsheet_id = st.secrets["SPREADSHEET_ID"]
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=SHEET_NAME,
            rows=1000,
            cols=len(HEADERS),
        )

    values = worksheet.get_all_values()

    if not values:
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
    elif values[0] != HEADERS:
        worksheet.clear()
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")

    return worksheet


def load_logs():
    worksheet = get_worksheet()
    records = worksheet.get_all_records()

    if not records:
        return pd.DataFrame(columns=HEADERS)

    return pd.DataFrame(records)


def save_log(row):
    worksheet = get_worksheet()

    worksheet.append_row(
        [row.get(col, "") for col in HEADERS],
        value_input_option="USER_ENTERED",
    )


# ==================================================
# 入力フォーム
# ==================================================

st.header("1. 市場チェック")

log_date = st.date_input("日付", value=date.today())

col1, col2 = st.columns(2)

with col1:
    st.subheader("日経平均")

    nikkei_direction = st.selectbox(
        "日経平均：上昇 / 下落",
        ["上昇", "下落", "横ばい", "わからない"]
    )

    nikkei_strength = st.selectbox(
        "日経平均：強さ",
        ["強い", "普通", "弱い", "わからない"]
    )

    nikkei_ma = st.selectbox(
        "日経平均：25MAとの位置",
        ["25MAより上", "25MA付近", "25MAより下", "わからない"]
    )

    nikkei_memo = st.text_area(
        "日経平均の感想",
        placeholder="例：25MA上で反発。大型株中心に買われた印象。"
    )

with col2:
    st.subheader("グロース市場")

    growth_strength = st.selectbox(
        "グロース市場：強さ",
        ["強い", "普通", "弱い", "わからない"]
    )

    growth_vs_nikkei = st.selectbox(
        "日経平均と比べて",
        ["日経より強い", "同じくらい", "日経より弱い", "わからない"]
    )

    small_stock_flow = st.selectbox(
        "小型株への資金流入",
        ["強そう", "普通", "弱そう", "わからない"]
    )

    growth_memo = st.text_area(
        "グロース市場の感想",
        placeholder="例：日経は強いがグロースは弱く、小型株には資金が来ていない印象。"
    )


# ==================================================
# テーマ観察
# ==================================================

st.header("2. テーマ観察")

themes = st.multiselect(
    "今日強かったテーマ",
    [
        "AI",
        "半導体",
        "防衛",
        "電力",
        "データセンター",
        "宇宙",
        "ロボット",
        "ゲーム",
        "銀行",
        "商社",
        "自動車",
        "小型グロース",
        "決算銘柄",
        "わからない"
    ]
)

theme_memo = st.text_area(
    "テーマの感想",
    placeholder="例：半導体大型が強く、グロースには資金が来ていない印象。"
)


# ==================================================
# 個別銘柄チェック
# ==================================================

st.header("3. 個別銘柄チェック")

code = st.text_input("コード", placeholder="例：7203")
stock_name = st.text_input("銘柄名", placeholder="例：トヨタ自動車")

reason = st.multiselect(
    "なぜ強かった？",
    [
        "決算",
        "上方修正",
        "テーマ",
        "高値更新",
        "出来高急増",
        "材料ニュース",
        "SNS話題",
        "わからない"
    ]
)

chart_features = st.multiselect(
    "チャート特徴",
    [
        "25MA上",
        "75MA上",
        "高値更新",
        "GU",
        "出来高急増",
        "ブレイクアウト",
        "高値圏ヨコヨコ",
        "押し目浅い",
        "わからない"
    ]
)

stock_memo = st.text_area(
    "個別銘柄の感想",
    placeholder="例：決算後にGU。その後も高値圏を維持しているが、すでに上がった後に見える。"
)


# ==================================================
# チャート画像アップロード
# ==================================================

st.header("4. チャート画像")

uploaded_file = st.file_uploader(
    "チャート画像をアップロード",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file is not None:
    st.image(
        uploaded_file,
        caption="アップロードしたチャート",
        use_container_width=True
    )

    st.success("チャート画像を読み込みました。")


# ==================================================
# ChatGPT答え合わせ用テキスト生成
# ==================================================

st.header("5. ChatGPT答え合わせ用テキスト")

prompt_text = f"""
このチャート画像を、株式投資の相場観察として解説してください。

目的は未来予測ではなく、
「観察・研究・答え合わせ」です。

以下の入力内容と、添付するチャート画像をもとに、
初心者にもわかるように解説してください。

==================================================
【日付】
==================================================

{log_date}

==================================================
【市場観察】
==================================================

■ 日経平均

・上昇 / 下落：{nikkei_direction}
・強さ：{nikkei_strength}
・25MAとの位置：{nikkei_ma}
・自分の感想：
{nikkei_memo}

---

■ グロース市場

・強さ：{growth_strength}
・日経平均と比べて：{growth_vs_nikkei}
・小型株への資金流入：{small_stock_flow}
・自分の感想：
{growth_memo}

==================================================
【テーマ観察】
==================================================

■ 今日強かったテーマ

{", ".join(themes) if themes else "未入力"}

■ テーマの感想

{theme_memo}

==================================================
【個別銘柄観察】
==================================================

■ コード

{code}

■ 銘柄名

{stock_name}

■ なぜ強かった？

{", ".join(reason) if reason else "未入力"}

■ チャート特徴

{", ".join(chart_features) if chart_features else "未入力"}

■ 自分の感想

{stock_memo}

==================================================
【見てほしいこと】
==================================================

以下の観点で答え合わせをしてください。

1. 自分の観察で合っている点
2. 追加で見るべき点
3. チャートが強く見えるポイント
4. チャートが弱く見えるポイント
5. 出来高の見方
6. 25MA・75MAの見方
7. 高値更新・GU・ブレイクアウトの見方
8. 翌日以降に観察すべきポイント
9. 研究ログとして残すべき気づき

注意：
売買推奨はしないでください。
断定的な未来予測はしないでください。
「観察・研究・学習」として解説してください。
"""

if st.button("ChatGPT答え合わせ用テキストを作成"):
    st.text_area(
        "この文章をコピーして、チャート画像と一緒にChatGPTへ貼ってください",
        value=prompt_text,
        height=600
    )


# ==================================================
# 今日の気づき
# ==================================================

st.header("6. 今日の気づき")

today_learning = st.text_area(
    "今日の気づき",
    placeholder="例：日経は強いがグロースは弱く、大型株中心の地合いに見えた。"
)

tomorrow_watch = st.text_area(
    "明日見ること",
    placeholder="例：今日強かった決算銘柄が翌日も出来高を維持するか見る。"
)


# ==================================================
# 保存処理
# ==================================================

st.header("7. 保存")

if st.button("Googleスプレッドシートに保存"):
    row = {
        "date": str(log_date),
        "nikkei_direction": nikkei_direction,
        "nikkei_strength": nikkei_strength,
        "nikkei_ma": nikkei_ma,
        "nikkei_memo": nikkei_memo,
        "growth_strength": growth_strength,
        "growth_vs_nikkei": growth_vs_nikkei,
        "small_stock_flow": small_stock_flow,
        "growth_memo": growth_memo,
        "themes": ",".join(themes),
        "theme_memo": theme_memo,
        "code": code,
        "stock_name": stock_name,
        "reason": ",".join(reason),
        "chart_features": ",".join(chart_features),
        "stock_memo": stock_memo,
        "today_learning": today_learning,
        "tomorrow_watch": tomorrow_watch,
    }

    try:
        save_log(row)
        st.success("Googleスプレッドシートに保存しました。")
    except Exception as e:
        st.error("保存に失敗しました。")
        st.exception(e)


# ==================================================
# 過去ログ表示
# ==================================================

st.header("8. 過去ログ")

if st.button("過去ログを読み込む"):
    try:
        df_log = load_logs()

        if df_log.empty:
            st.info("まだ保存された観察ログはありません。")
        else:
            st.dataframe(df_log.tail(20), use_container_width=True)

    except Exception as e:
        st.error("過去ログの読み込みに失敗しました。")
        st.exception(e)
