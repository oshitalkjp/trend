import streamlit as st
import google.generativeai as genai
from pytrends.request import TrendReq
import pandas as pd

# ページ設定
st.set_page_config(page_title="TrendCast - 超速トレンドまとめ", layout="wide")

# タイトルと説明
st.title("🚀 TrendCast: トレンド抽出＆台本化")
st.markdown("最新のトレンドを取得し、動画やブログ用に「超わかりやすく」まとめます。")

# サイドバー：設定
st.sidebar.header("設定")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
target_mode = st.sidebar.radio("作成モード", ["YouTubeショート/TikTok用", "ブログ/ニュース記事用", "辛口コメンテーター風"])

# Geminiの設定
if api_key:
    genai.configure(api_key=api_key)

# 関数: Googleトレンド取得
def get_trends():
    pytrends = TrendReq(hl='ja-JP', tz=540)
    try:
        # 日本の急上昇ワードを取得
        trending_searches_df = pytrends.trending_searches(pn='japan')
        return trending_searches_df.head(10)[0].tolist() # 上位10件
    except Exception as e:
        st.error(f"トレンド取得エラー: {e}")
        return []

# 関数: AIによる要約と台本化
def generate_script(keyword, mode):
    if not api_key:
        return "⚠️ APIキーを設定してください"
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    キーワード「{keyword}」について、Web上の情報を想定して解説してください。
    
    【目的】
    {mode}としてアウトプットを作成する。
    
    【条件】
    - 専門用語は使わず、中学生でもわかるように。
    - 視聴者の興味を引く「フック（掴み）」を入れること。
    - 結論→理由→具体例の順で構成する。
    - 箇条書きや改行を使い、読みやすく整形する。
    """
    
    with st.spinner('AIが執筆中...'):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"エラーが発生しました: {e}"

# --- メイン画面 ---

# トレンド取得ボタン
if st.button("🔥 最新トレンドを取得"):
    trends = get_trends()
    if trends:
        st.session_state['trends'] = trends
        st.success("トレンドを取得しました！")

# トレンド一覧表示
if 'trends' in st.session_state:
    selected_trend = st.selectbox("ネタにするキーワードを選んでください", st.session_state['trends'])
    
    if st.button("✨ このネタで台本を作る"):
        script = generate_script(selected_trend, target_mode)
        st.subheader(f"「{selected_trend}」の台本案")
        st.info(target_mode)
        st.text_area("出力結果（コピーして使えます）", script, height=400)
        
else:
    st.info("まずは「最新トレンドを取得」ボタンを押してください。")

# フッター
st.divider()
st.caption("Created for Creator Support | Powerd by Google Trends & Gemini")
