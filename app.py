import streamlit as st
import google.generativeai as genai
import feedparser
import time

# -------------------------
# 1. ページ設定 & デザイン調整
# -------------------------
st.set_page_config(
    page_title="TrendCast Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS（見やすくする）
st.markdown("""
<style>
    .stButton button {width: 100%; border-radius: 8px; font-weight: bold;}
    .block-container {padding-top: 2rem;}
    div[data-testid="stExpander"] {border: 1px solid #ddd; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 2. 関数定義
# -------------------------

# Googleトレンド（RSS）から取得する安定版関数
@st.cache_data(ttl=3600) # 1時間キャッシュして高速化
def get_trends_rss():
    # Googleトレンドの日本版RSS
    rss_url = "https://trends.google.co.jp/trends/trendingsearches/daily/rss?geo=JP"
    feed = feedparser.parse(rss_url)
    
    trends = []
    for entry in feed.entries:
        trends.append({
            "title": entry.title,
            "link": entry.link,
            "traffic": entry.get('ht_approx_traffic', 'N/A'), # 推定検索数
            "pubDate": entry.published
        })
    return trends

# AI生成関数
def generate_content(api_key, topic, mode):
    if not api_key:
        return "⚠️ エラー: 左下の設定欄にAPIキーを入力してください。"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompts = {
        "YouTubeショート/TikTok": f"""
        キーワード「{topic}」について、バズるショート動画の台本を作成してください。
        【構成】
        1. タイトル: インパクト重視（20文字以内）
        2. フック: 最初の1秒で引きつける強烈な一言
        3. 本文: 3段落構成（オチをつける）
        4. ハッシュタグ: 5つ
        【口調】: テンポよく、YouTuberっぽく。
        """,
        "ブログ/ニュース解説": f"""
        キーワード「{topic}」について、Webメディア用の解説記事を作成してください。
        【構成】
        1. 記事タイトル: SEOを意識した30文字
        2. リード文: 読者の興味を惹く導入
        3. 見出し1: 何が起きたのか（事実）
        4. 見出し2: なぜ話題なのか（背景・反応）
        5. まとめ
        【口調】: 論理的でわかりやすく、親しみやすく。
        """,
        "X (Twitter) ポスト": f"""
        キーワード「{topic}」について、X（旧Twitter）で拡散されやすいポストを作成してください。
        【条件】
        - 140文字ギリギリを攻める
        - 共感を呼ぶ、または議論を呼ぶ内容にする
        - 箇条書きを活用する
        """
    }
    
    prompt = prompts.get(mode, prompts["YouTubeショート/TikTok"])
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI生成エラー: {e}"

# -------------------------
# 3. アプリのUI構築
# -------------------------

# --- サイドバー（設定 & トレンドリスト） ---
with st.sidebar:
    st.header("⚡ TrendCast Pro")
    
    # APIキー設定（Secrets対応）
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key: 連携済み")
    else:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="ここにキーを貼る")
        st.caption("[キーの取得はこちら](https://aistudio.google.com/app/apikey)")

    st.divider()
    
    st.subheader("📈 急上昇ランキング")
    if st.button("🔄 最新情報を更新"):
        st.cache_data.clear()
        st.rerun()

    # トレンド取得
    trends_data = get_trends_rss()
    
    # トレンド選択用ラジオボタン（見た目をリスト風に）
    trend_titles = [f"{t['title']} ({t['traffic']})" for t in trends_data]
    selected_trend_str = st.radio("分析するネタを選択:", trend_titles)
    
    # 選択されたトレンドのデータを取り出す
    selected_index = trend_titles.index(selected_trend_str)
    current_trend = trends_data[selected_index]

# --- メイン画面 ---
st.subheader(f"ネタ候補: {current_trend['title']}")

# リンクボタン表示
st.markdown(f"🔗 [ニュース検索結果を見る]({current_trend['link']})", unsafe_allow_html=True)

st.divider()

# 生成モード選択タブ
tab1, tab2, tab3 = st.tabs(["📱 ショート動画", "📝 ブログ記事", "🐦 Xポスト"])

# 生成実行と表示
if api_key:
    # タブ1: ショート動画
    with tab1:
        if st.button("🚀 動画台本を生成", key="btn_video"):
            with st.spinner("AIが台本を執筆中..."):
                result = generate_content(api_key, current_trend['title'], "YouTubeショート/TikTok")
                st.text_area("出力結果", result, height=400)
                
    # タブ2: ブログ
    with tab2:
        if st.button("🖋 記事構成を生成", key="btn_blog"):
            with st.spinner("AIが記事を構成中..."):
                result = generate_content(api_key, current_trend['title'], "ブログ/ニュース解説")
                st.text_area("出力結果", result, height=400)

    # タブ3: Xポスト
    with tab3:
        if st.button("🐦 ポストを作成", key="btn_x"):
            with st.spinner("AIがポストを作成中..."):
                result = generate_content(api_key, current_trend['title'], "X (Twitter) ポスト")
                st.text_area("出力結果", result, height=200)
else:
    st.warning("👈 まずはサイドバーでAPIキーを設定してください")
