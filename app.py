import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import re

# -------------------------
# 1. 基本設定
# -------------------------
st.set_page_config(page_title="TrendCast: X Edition", page_icon="❌", layout="wide")

# デザイン調整
st.markdown("""
<style>
    .stButton button {width: 100%; font-weight: bold; border-radius: 8px;}
    div[role="radiogroup"] label {padding: 10px; background: #f4f4f4; border-radius: 5px; margin-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 2. Xトレンド取得ロジック（Yahoo経由）
# -------------------------
@st.cache_data(ttl=300) # 5分ごとに更新
def get_x_trends():
    # Xのトレンドと連動しているYahooリアルタイム検索をターゲットにする
    url = "https://search.yahoo.co.jp/realtime"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        trends = []
        # Yahooリアルタイムのランキング構造解析
        # 構造が変わってもある程度拾えるように汎用的なクラス検索を行う
        ranking_items = soup.find_all('li', class_=re.compile("Ranking_item"))

        # もしクラス名が変わっていて取れない場合の予備検索
        if not ranking_items:
             ranking_items = soup.select('div[class*="Ranking_item"] a')

        for idx, item in enumerate(ranking_items):
            if idx >= 20: break # TOP20まで
            
            # テキスト抽出
            title = item.get_text(strip=True)
            # 順位番号（1位など）がテキストに含まれる場合があるので削除（整形）
            title = re.sub(r'^\d+位\s*', '', title)
            
            # リンク取得
            link_tag = item.find('a') if item.name != 'a' else item
            link = link_tag['href'] if link_tag else url
            
            trends.append({
                "rank": idx + 1,
                "title": title,
                "link": link
            })
            
        return trends

    except Exception as e:
        return []

# -------------------------
# 3. AI生成ロジック
# -------------------------
def generate_content(api_key, topic, mode):
    if not api_key:
        return "⚠️ APIキーが設定されていません。"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # ユーザーの要望に合わせて台本精度を強化
    prompts = {
        "動画台本": f"""
        キーワード「{topic}」について、X（Twitter）での反応を予測してショート動画の台本を作れ。
        【条件】
        - 冒頭：視聴者が「えっ？」となる強いフック。
        - 内容：事実を淡々と述べるのではなく、ネット民の反応や議論のポイントを盛り込む。
        - 結び：コメント欄への誘導（「みんなはどう思う？」など）。
        - 構成：タイトル、フック、本文（30秒分）、オチ。
        """,
        "まとめニュース記事": f"""
        キーワード「{topic}」について、まとめサイト風の記事を作成せよ。
        【条件】
        - タイトル：クリックしたくなる煽り気味のもの。
        - 構成：
          1. 何が起きた？（3行で要約）
          2. ネットの反応（肯定的な意見と否定的な意見を架空のコメント形式で）
          3. 管理人の所感
        """,
        "Xポスト作成": f"""
        キーワード「{topic}」を使って、インプレッションを稼ぐポストを作れ。
        - 140字以内
        - 共感を呼ぶか、あえて反論を招く文章
        - 関連ハッシュタグ3つ
        """
    }
    
    try:
        response = model.generate_content(prompts[mode])
        return response.text
    except Exception as e:
        return f"生成エラー: {e}"

# -------------------------
# 4. UI構築
# -------------------------
with st.sidebar:
    st.title("❌ X-Trend Cast")
    
    # APIキー入力
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key: OK")
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    
    if st.button("🔥 Xトレンド更新"):
        st.cache_data.clear()
        st.rerun()
    
    # データ取得
    trends = get_x_trends()
    
    if trends:
        trend_options = [f"{t['rank']}位: {t['title']}" for t in trends]
        selected_option = st.radio("ネタ選択", trend_options)
        
        # 選択データ取得
        selected_index = trend_options.index(selected_option)
        current_trend = trends[selected_index]
    else:
        current_trend = None
        st.error("トレンド取得失敗。時間をおいて再試行してください。")

# メイン画面
if current_trend:
    st.header(f"話題: {current_trend['title']}")
    st.markdown(f"[Yahooリアルタイム検索で見る]({current_trend['link']})")
    
    tab1, tab2, tab3 = st.tabs(["🎥 動画台本", "📑 まとめ記事", "🐦 Xポスト"])
    
    with tab1:
        if st.button("台本生成", key="v"):
            st.write(generate_content(api_key, current_trend['title'], "動画台本"))
    with tab2:
        if st.button("記事生成", key="b"):
            st.write(generate_content(api_key, current_trend['title'], "まとめニュース記事"))
    with tab3:
        if st.button("ポスト生成", key="x"):
            st.write(generate_content(api_key, current_trend['title'], "Xポスト作成"))

else:
    st.info("サイドバーの「Xトレンド更新」を押してデータを取得してください。")
