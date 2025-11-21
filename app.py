import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import time

# -------------------------
# 1. 基本設定
# -------------------------
st.set_page_config(page_title="TrendCast: X-Killer", page_icon="❌", layout="wide")

st.markdown("""
<style>
    .stButton button {width: 100%; font-weight: bold; border-radius: 8px; background-color: #1DA1F2; color: white;}
    div[role="radiogroup"] label {padding: 10px; background: #f4f4f4; border-radius: 5px; margin-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 2. Xトレンド取得 (Twittrend経由)
# -------------------------
@st.cache_data(ttl=180) # 3分ごとに更新
def get_x_trends_robust():
    # Yahooがダメなら、Twittrend（Xのトレンドまとめサイト）から抜く
    target_url = "https://twittrend.jp/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        trends = []
        
        # Twittrendの日本全体のランキングを取得
        # id="now" の中の ul > li を探す
        now_div = soup.find('div', id='now')
        if now_div:
            items = now_div.find_all('li')
            for idx, item in enumerate(items):
                if idx >= 20: break # TOP20
                
                title_tag = item.find('p', class_='title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # リンク生成（Xの検索ページへ飛ばす）
                    link = f"https://twitter.com/search?q={title}"
                    
                    trends.append({
                        "rank": idx + 1,
                        "title": title,
                        "link": link
                    })
        
        return trends

    except Exception as e:
        st.error(f"データソース接続エラー: {e}")
        return []

# -------------------------
# 3. AI生成ロジック
# -------------------------
def generate_content(api_key, topic, mode):
    if not api_key:
        return "⚠️ エラー: サイドバーにAPIキーを入れてください。"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompts = {
        "動画": f"キーワード「{topic}」について、X（Twitter）民が食いつくショート動画の台本を作れ。\n構成：衝撃的なタイトル、冒頭のフック、本題（ネットの反応含む）、オチ。\n口調：辛口かつテンポよく。",
        "ニュース": f"キーワード「{topic}」について、まとめサイト風の記事を作れ。\n構成：煽りタイトル、3行要約、肯定・否定それぞれのネットの反応（架空）、結論。",
        "ポスト": f"キーワード「{topic}」について、インプレッション稼ぎ用のXポストを作れ。\n条件：140字以内、問いかけを入れる、ハッシュタグ3つ。"
    }
    
    try:
        response = model.generate_content(prompts[mode])
        return response.text
    except Exception as e:
        return f"AIエラー: {e}"

# -------------------------
# 4. UIメイン
# -------------------------
with st.sidebar:
    st.header("❌ X-Trend Cast")
    
    # APIキー
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key: OK")
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    
    if st.button("🔥 トレンド強制更新"):
        st.cache_data.clear()
        st.rerun()
    
    # データ取得実行
    trends = get_x_trends_robust()
    
    if trends:
        trend_list = [f"{t['rank']}位: {t['title']}" for t in trends]
        selected_label = st.radio("トレンド選択", trend_list)
        
        # 選択データ抽出
        idx = trend_list.index(selected_label)
        current_trend = trends[idx]
    else:
        current_trend = None
        st.error("トレンド取得失敗。ソースサイトがダウンしている可能性があります。")

# 右側エリア
if current_trend:
    st.title(f"話題: {current_trend['title']}")
    st.markdown(f"🔗 [Xで検索する]({current_trend['link']})")
    
    tab1, tab2, tab3 = st.tabs(["🎥 動画台本", "📑 まとめニュース", "🐦 拡散ポスト"])
    
    with tab1:
        if st.button("台本生成", key="v"):
            st.write(generate_content(api_key, current_trend['title'], "動画"))
    with tab2:
        if st.button("記事生成", key="n"):
            st.write(generate_content(api_key, current_trend['title'], "ニュース"))
    with tab3:
        if st.button("ポスト生成", key="p"):
            st.write(generate_content(api_key, current_trend['title'], "ポスト"))

else:
    st.warning("👈 サイドバーの更新ボタンを押してください")
