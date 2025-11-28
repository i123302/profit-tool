import streamlit as st
import urllib.request
import json
import pandas as pd  # 用于生成 Excel/CSV 数据

# === 页面设置 (Page Config) ===
st.set_page_config(page_title="Naver 选品数据导出", page_icon="📥", layout="wide")

# === API 设置 (API Key) ===
client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 侧边栏 (Sidebar) ===
with st.sidebar:
    st.header("⚙️ 환경 설정 (Settings)")
    exchange_rate = st.number_input("현재 환율 (1 RMB = ? KRW)", value=195)
    shipping_cost = st.number_input("예상 배송비 (KRW)", value=3000)
    st.divider()
    st.info("💡 검색 후 '엑셀 다운로드' 버튼을 누르면 데이터를 저장할 수 있습니다.")

# === 主标题 (Main Title) ===
st.title("🇰🇷 Naver 选品数据分析 & 导出工具")
st.markdown("### 📥 搜索 -> 分析 -> 导出 Excel")

# === 搜索区 (Search Area) ===
with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("상품 키워드 (Keyword)", placeholder="예: 무선 청소기")
    with col2:
        cost_rmb = st.number_input("소싱 원가 (RMB)", value=0)
    with col3:
        st.write("") 
        st.write("") 
        btn_start = st.button("분석 시작 (Start) 🔍", type="primary", use_container_width=True)

# === 核心逻辑 (Core Logic) ===
if btn_start:
    if not keyword:
        st.warning("⚠️ 검색어를 입력해주세요!")
    else:
        # 1. 成本计算
        total_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        if cost_rmb > 0:
            st.success(f"📊 **원가 기준**: {cost_rmb}위안 × {exchange_rate} + 배송비 = **{total_cost_krw:,.0f} 원**")
        st.divider()

        # 2. 调用 API
        encText = urllib.parse.quote(keyword)
        # 增加搜索数量到 50 个，方便导出分析
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=50&sort=sim"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('데이터 수집 및 엑셀 생성 중... (Generating Excel...)'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            if not data['items']:
                st.error("❌ 검색 결과가 없습니다.")
            else:
                # 3. 数据处理 & 导出准备
                excel_data = [] # 用来存 Excel 数据的列表
                
                for item in data['items']:
                    # 基础信息
                    name = item['title'].replace('<b>', '').replace('</b>', '')
                    lprice = int(item['lprice']) # 现价
                    hprice = int(item['hprice']) if item['hprice'] else 0 # 原价
                    mall_name = item['mallName']
                    link = item['link']
                    img_url = item['image']
                    brand = item.get('brand', '')
                    maker = item.get('maker', '')
                    category = f"{item['category1']}>{item['category2']}>{item['category3']}"

                    # 利润计算
                    profit = lprice - total_cost_krw
                    profit_rate = (profit / lprice) * 100 if lprice > 0 else 0
                    
                    # 收集数据到列表 (用于 Excel)
                    excel_data.append({
                        "상품명 (Name)": name,
                        "판매가 (Price)": lprice,
                        "정상가 (Original Price)": hprice if hprice > 0 else "-",
                        "예상 마진 (Profit)": profit if cost_rmb > 0 else 0,
                        "마진율 (%)": f"{profit_rate:.1f}%" if cost_rmb > 0 else "-",
                        "쇼핑몰 (Mall)": mall_name,
                        "브랜드 (Brand)": brand,
                        "제조사 (Maker)": maker,
                        "카테고리 (Category)": category,
                        "링크 (Link)": link
                    })

                    # 4. 界面展示 (只显示前 20 个，避免网页太长)
                    if len(excel_data) <= 20: 
                        with st.container():
                            c1, c2 = st.columns([1, 4])
                            with c1:
                                st.image(img_url, use_container_width=True)
                            with c2:
                                st.markdown(f"**[{name}]({link})**")
                                
                                # 参数栏
                                st.caption(f"🏷️ 브랜드: {brand} | 🏭 제조: {maker} | 📂 {category}")
                                
                                # 价格对比
                                col_p1, col_p2, col_p3 = st.columns(3)
                                with col_p1:
                                    st.metric("판매가 (Sale)", f"₩{lprice:,}")
                                with col_p2:
                                    if hprice > 0:
                                        st.metric("정상가 (Original)", f"₩{hprice:,}")
                                    else:
                                        st.metric("정상가", "-")
                                with col_p3:
                                    if cost_rmb > 0:
                                        color = "normal" if profit > 0 else "inverse"
                                        st.metric("예상 마진", f"₩{profit:,}", f"{profit_rate:.1f}%", delta_color=color)
                        st.divider()

                # === 5. 📥 엑셀(CSV) 다운로드 버튼 (核心功能) ===
                if excel_data:
                    df = pd.DataFrame(excel_data)
                    # 转换成 CSV 格式 (utf-8-sig 是为了保证 Excel 打开韩文不乱码)
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    
                    st.sidebar.markdown("### 📥 데이터 다운로드")
                    st.sidebar.download_button(
                        label="📄 엑셀(CSV)로 저장하기 (Download Excel)",
                        data=csv,
                        file_name=f'{keyword}_market_analysis.csv',
                        mime='text/csv',
                        type='primary'
                    )
                    st.sidebar.success(f"총 {len(excel_data)}개의 데이터가 준비되었습니다!")

        except Exception as e:
            st.error(f"Error: {e}")
