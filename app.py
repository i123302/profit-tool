import streamlit as st
import urllib.request
import json
import pandas as pd
import altair as alt
from collections import Counter
import re

# === 页面配置 ===
st.set_page_config(page_title="Naver AI Analyst", page_icon="🤖", layout="wide")

# === 🔐 安全验证 ===
PASSWORD = "8888" 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.password_input == PASSWORD:
        st.session_state.authenticated = True
    else:
        st.error("🚫 암호 오류 (密码错误)")

if not st.session_state.authenticated:
    st.markdown("### 🤖 AI Market Analyst Login")
    st.text_input("Access Code:", type="password", key="password_input", on_change=check_password)
    st.stop()

# ==========================================
# 🔓 AI 分析界面
# ==========================================

client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 🤖 AI 分析核心函数 ===
def analyze_title_tags(title):
    """从标题中提取核心卖点标签"""
    tags = []
    # 这里的词库可以根据你的品类不断扩充
    keywords = {
        'Spec': ['무선', '유선', '블루투스', '저소음', '기계식', '게이밍', 'RGB', 'LED', 'C타입'],
        'Feature': ['방수', '초경량', '대용량', '미니', '휴대용', '접이식'],
        'Target': ['사무용', '선물', '학생', '여성'],
        'Shipping': ['해외직구', '당일발송', '무료배송']
    }
    
    for category, words in keywords.items():
        for word in words:
            if word in title:
                tags.append(word)
    return tags

def calculate_listing_score(item):
    """计算 AI 推荐分 (0-100)"""
    score = 60 # 基础分
    
    # 1. 品牌加分
    if item['brand']: score += 10
    if item['maker']: score += 5
    
    # 2. 标题质量加分 (包含关键信息的多少)
    title_len = len(item['title'])
    if title_len > 20: score += 10 # 标题够长，信息量大
    
    # 3. 平台加分
    if '쿠팡' in item['mallName'] or '스마트스토어' in item['mallName']:
        score += 10
    
    # 4. 图片质量 (如果有原价对比)
    if item['hprice']: score += 5
    
    return min(score, 100)

# === 侧边栏 ===
with st.sidebar:
    st.header("🤖 AI 분석 설정")
    exchange_rate = st.number_input("환율 (Exchange Rate)", value=195)
    shipping_cost = st.number_input("배송비 (Shipping Cost)", value=3000)
    st.divider()
    platform_fee = st.slider("수수료 (Fee %)", 0.0, 15.0, 5.5)
    vat_tax = st.slider("부가세 (VAT %)", 0.0, 20.0, 10.0)
    st.info("💡 AI가 제목을 분석하여 '제품 특징'을 추출합니다.")

st.title("🤖 Naver AI Market Analyst V10.0")

# === 搜索区 ===
with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("분석 키워드 (Keyword)", placeholder="예: 무선 기계식 키보드")
    with col2:
        cost_rmb = st.number_input("소싱 원가 (RMB)", value=0)
    with col3:
        st.write("") 
        st.write("") 
        btn_start = st.button("AI 분석 시작 🧠", type="primary", use_container_width=True)

# === 核心逻辑 ===
if btn_start:
    if not keyword:
        st.warning("⚠️ 키워드를 입력해주세요")
    else:
        base_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        
        # 抓取更多数据以进行 AI 分析 (50条)
        encText = urllib.parse.quote(keyword)
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=50&sort=sim"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('🤖 AI가 상품 데이터를 해부하고 있습니다...'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            if not data['items']:
                st.error("❌ 데이터가 없습니다.")
            else:
                # === 数据预处理 ===
                df_list = []
                all_titles = "" # 用于生成词云
                
                for item in data['items']:
                    lprice = int(item['lprice'])
                    title = item['title'].replace('<b>', '').replace('</b>', '')
                    all_titles += title + " "
                    
                    # 利润计算
                    fee = lprice * (platform_fee/100)
                    tax = lprice * (vat_tax/100)
                    net_profit = lprice - (base_cost_krw + fee + tax)
                    margin = (net_profit / lprice) * 100 if lprice > 0 else 0
                    
                    # 🤖 AI 分析
                    ai_tags = analyze_title_tags(title) # 提取标签
                    ai_score = calculate_listing_score(item) # 计算分数
                    
                    df_list.append({
                        "Title": title,
                        "Price": lprice,
                        "NetProfit": net_profit,
                        "Margin": margin,
                        "Image": item['image'],
                        "Link": item['link'],
                        "Mall": item['mallName'],
                        "AI_Tags": ai_tags,
                        "AI_Score": ai_score
                    })
                
                df = pd.DataFrame(df_list)

                # === 1. 🤖 AI 市场洞察 (Market Insight) ===
                st.markdown("### 🧠 AI 시장 인사이트 (Market Insights)")
                
                # 词频分析 (找出标题里出现最多的词)
                words = re.findall(r'[가-힣a-zA-Z]+', all_titles)
                # 过滤掉关键词本身和无关词
                stop_words = [keyword.replace(" ", ""), '및', '용', '형', '의', '등'] 
                filtered_words = [w for w in words if len(w) > 1 and w not in stop_words]
                common_words = Counter(filtered_words).most_common(5)
                
                insight_cols = st.columns(3)
                with insight_cols[0]:
                    st.info(f"🔥 **가장 핫한 키워드 (Hot Keywords)**")
                    for word, count in common_words:
                        st.markdown(f"- **{word}**: {count}회 등장")
                
                with insight_cols[1]:
                    avg_price = df['Price'].mean()
                    st.success(f"💰 **평균 시장가**: ₩{int(avg_price):,}")
                    st.caption("이 가격보다 낮으면 경쟁력이 있습니다.")
                    
                with insight_cols[2]:
                    high_score_items = df[df['AI_Score'] >= 90].shape[0]
                    st.warning(f"⭐ **고품질 리스팅**: {high_score_items}개")
                    st.caption("경쟁사들의 상세페이지 퀄리티가 높습니다.")

                st.divider()

                # === 2. 详细列表 (带 AI 标签) ===
                st.markdown("### 📋 AI 분석 리스트")
                
                for index, row in df.iterrows():
                    with st.container():
                        c1, c2, c3 = st.columns([1, 3, 1])
                        
                        with c1:
                            st.image(row['Image'], use_container_width=True)
                            st.caption(f"🤖 AI Score: **{row['AI_Score']}**")
                        
                        with c2:
                            st.markdown(f"**[{row['Title']}]({row['Link']})**")
                            
                            # 显示 AI 提取的标签
                            if row['AI_Tags']:
                                tags_html = ""
                                for tag in row['AI_Tags']:
                                    tags_html += f"<span style='background-color:#e1f5fe; color:#0277bd; padding:2px 6px; border-radius:4px; margin-right:4px; font-size:12px'>#{tag}</span>"
                                st.markdown(tags_html, unsafe_allow_html=True)
                            else:
                                st.caption("특이사항 없음 (无特殊标签)")
                                
                            st.write("")
                            st.caption(f"🏪 {row['Mall']}")

                        with c3:
                            st.metric("판매가", f"₩{row['Price']:,}")
                            
                            if cost_rmb > 0:
                                color = "normal" if row['NetProfit'] > 0 else "inverse"
                                st.metric("순수익", f"₩{int(row['NetProfit']):,}", f"{row['Margin']:.1f}%", delta_color=color)
                            
                            # 评论直达按钮
                            st.link_button("💬 리뷰 보기 (Reviews)", row['Link'])
                            
                        st.divider()

        except Exception as e:
            st.error(f"Error: {e}")
