import streamlit as st
import urllib.request
import json

# === 페이지 설정 (页面设置) ===
st.set_page_config(page_title="마켓 소싱 분석기", page_icon="🇰🇷", layout="wide")

# === API 설정 (API Key) ===
client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 사이드바 설정 (Sidebar) ===
with st.sidebar:
    st.header("⚙️ 환경 설정 (Settings)")
    exchange_rate = st.number_input("현재 환율 (1 RMB = ? KRW)", value=195)
    shipping_cost = st.number_input("개당 예상 배송비 (KRW)", value=3000)
    st.divider()
    st.info("💡 Tip: 1688 소싱 단가를 입력하면 마진율이 자동 계산됩니다.")

# === 메인 타이틀 (Main Title) ===
st.title("🇰🇷 이커머스 시장 분석 & 마진 계산기")
st.markdown("### 🔍 경쟁사 가격/채널/마진 분석 (Naver & Coupang)")

# === 입력 섹션 (Input Section) ===
with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("상품 키워드 (Keyword)", placeholder="예: 기계식 키보드")
    with col2:
        cost_rmb = st.number_input("소싱 원가 (RMB/위안)", value=0)
    with col3:
        st.write("") 
        st.write("") 
        btn_start = st.button("분석 시작 (Start) 🚀", type="primary", use_container_width=True)

# === 핵심 로직 (Core Logic) ===
if btn_start:
    if not keyword:
        st.warning("⚠️ 키워드를 입력해주세요! (Please enter a keyword)")
    else:
        # 1. 원가 계산 (Cost Calculation)
        total_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        if cost_rmb > 0:
            st.success(f"📊 **원가 분석**: {cost_rmb}위안 × {exchange_rate} + 배송비 = **{total_cost_krw:,.0f} 원** (손익분기점)")
        st.divider()

        # 2. API 호출 (Call Naver API)
        encText = urllib.parse.quote(keyword)
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=30&sort=sim"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('데이터 분석 중... (Analyzing data...)'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            if not data['items']:
                st.error("❌ 검색 결과가 없습니다.")
            else:
                for item in data['items']:
                    name = item['title'].replace('<b>', '').replace('</b>', '')
                    lprice = int(item['lprice'])
                    mall_name = item['mallName']
                    link = item['link']
                    img_url = item['image']
                    
                    # 마진 계산 (Profit Calculation)
                    profit = lprice - total_cost_krw
                    profit_rate = (profit / lprice) * 100 if lprice > 0 else 0
                    
                    # === 플랫폼 식별 (Platform Detection) ===
                    is_coupang = False
                    if '쿠팡' in mall_name or 'Coupang' in mall_name:
                        is_coupang = True
                        mall_badge = "🚀 쿠팡 (Coupang)"
                        badge_color = "#e60f0f" # Red
                        bg_color = "#ffe6e6"
                    elif '스마트스토어' in mall_name or 'SmartStore' in mall_name:
                        mall_badge = "💚 스마트스토어"
                        badge_color = "#03c75a" # Green
                        bg_color = "#e6fff2"
                    else:
                        mall_badge = f"🏪 {mall_name}"
                        badge_color = "#555"
                        bg_color = "#f0f2f6"

                    # 액세서리 필터링 (Filter low price items)
                    if cost_rmb > 0 and lprice < (total_cost_krw * 0.4):
                        continue

                    # === UI 디스플레이 (UI Display) ===
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        
                        # 이미지 (Image)
                        with c1:
                            st.image(img_url, use_container_width=True)
                        
                        # 상세 정보 (Details)
                        with c2:
                            st.markdown(f"### [{name}]({link})")
                            
                            # 배지 표시 (Badge)
                            st.markdown(f"""
                            <span style='background-color:{bg_color}; color:{badge_color}; padding:4px 8px; border-radius:4px; font-weight:bold; border:1px solid {badge_color}'>
                            {mall_badge}
                            </span>
                            """, unsafe_allow_html=True)
                            
                            st.write("")
                            
                            # 가격 및 마진 (Price & Profit)
                            cp1, cp2 = st.columns(2)
                            with cp1:
                                st.metric("판매가 (Price)", f"₩{lprice:,}")
                            with cp2:
                                if cost_rmb > 0:
                                    if profit > 0:
                                        st.metric("예상 마진 (Profit)", f"₩{profit:,}", f"{profit_rate:.1f}%")
                                    else:
                                        st.metric("예상 마진 (Profit)", f"₩{profit:,}", f"{profit_rate:.1f}%", delta_color="inverse")
                                else:
                                    st.metric("원가 미입력", "-")
                    st.divider()

        except Exception as e:
            st.error(f"Error: {e}")
