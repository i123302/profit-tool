import streamlit as st
import urllib.request
import json

# === 0. 页面基础设置 ===
st.set_page_config(page_title="Naver Market Analyzer", page_icon="🇰🇷", layout="wide")

# === 1. 你的通行证 (API Key) ===
client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 2. 侧边栏 (设置区) ===
with st.sidebar:
    st.header("⚙️ 환경 설정 (环境设置)")
    exchange_rate = st.number_input("환율 (汇率: 1 RMB = ? KRW)", value=195)
    shipping_cost = st.number_input("배송비 (单件运费 KRW)", value=3000)
    st.divider()
    st.info("💡 Tip: 원가를 입력하면 마진율을 자동으로 계산합니다.")

# === 3. 主标题 ===
st.title("🇰🇷 스마트스토어 시장 분석기 (市场分析器)")
st.markdown("Naver Shopping의 실시간 데이터를 분석합니다.")

# === 4. 搜索输入区 ===
with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("검색어 입력 (输入韩语关键词)", placeholder="예: 기계식 키보드")
    with col2:
        cost_rmb = st.number_input("중국 소싱 원가 (输入进货价 RMB)", value=0)
    with col3:
        st.write("") 
        st.write("") 
        btn_start = st.button("분석 시작 (开始分析) 🔍", type="primary", use_container_width=True)

# === 5. 核心分析逻辑 ===
if btn_start:
    if not keyword:
        st.warning("⚠️ 검색어를 입력해주세요! (请输入关键词)")
    else:
        # 计算总成本
        total_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        
        # 显示成本概览
        if cost_rmb > 0:
            st.success(f"📊 **원가 분석**: 소싱가 {cost_rmb}위안 + 배송비 = **{total_cost_krw:,.0f} 원** (BEP 손익분기점)")
        
        st.divider()

        # 调用 API
        encText = urllib.parse.quote(keyword)
        # display=20 (看前20个), sort=sim (按相关度排序)
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=20&sort=sim"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('Naver 데이터를 불러오는 중... (正在获取数据)'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            if not data['items']:
                st.error("❌ 검색 결과가 없습니다. (没找到结果)")
            else:
                # 遍历结果
                for item in data['items']:
                    # 数据清洗
                    name = item['title'].replace('<b>', '').replace('</b>', '')
                    lprice = int(item['lprice']) # 最低价/销售价
                    hprice = int(item['hprice']) if item['hprice'] else 0 # 原价(有的没填)
                    
                    brand = item.get('brand', 'Unknown') # 品牌
                    maker = item.get('maker', 'Unknown') # 制造商
                    
                    # 分类路径
                    category = f"{item['category1']} > {item['category2']} > {item['category3']}"
                    if item['category4']:
                        category += f" > {item['category4']}"
                    
                    img_url = item['image']
                    link = item['link']

                    # 利润计算
                    profit = lprice - total_cost_krw
                    if lprice > 0:
                        profit_rate = (profit / lprice) * 100
                    else:
                        profit_rate = 0

                    # 过滤配件
                    if cost_rmb > 0 and lprice < (total_cost_krw * 0.5):
                        continue

                    # === 界面展示 (卡片式) ===
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        
                        # 左侧：大图
                        with c1:
                            st.image(img_url, use_container_width=True)
                            st.caption(f"🆔 {item['productId']}")
                        
                        # 右侧：详细信息
                        with c2:
                            # 1. 标题和链接
                            st.markdown(f"### [{name}]({link})")
                            
                            # 2. 核心参数 (Tags)
                            st.markdown(f"""
                            <span style='background-color:#f0f2f6; padding:4px 8px; border-radius:4px;'>🏷️ 브랜드: **{brand}**</span> 
                            <span style='background-color:#f0f2f6; padding:4px 8px; border-radius:4px;'>🏭 제조사: **{maker}**</span>
                            """, unsafe_allow_html=True)
                            
                            st.caption(f"📂 카테고리(分类): {category}")
                            
                            st.divider()
                            
                            # 3. 价格分析区
                            p1, p2, p3 = st.columns(3)
                            with p1:
                                st.metric("판매가 (销售价)", f"₩{lprice:,}")
                            with p2:
                                if hprice > 0:
                                    discount = ((hprice - lprice) / hprice) * 100
                                    st.metric("정상가 (原价)", f"₩{hprice:,}", f"-{discount:.0f}% 할인")
                                else:
                                    st.metric("정상가 (原价)", "-")
                            with p3:
                                if cost_rmb > 0:
                                    if profit > 0:
                                        st.metric("예상 마진 (利润)", f"₩{profit:,}", f"{profit_rate:.1f}%")
                                    else:
                                        st.metric("예상 마진 (利润)", f"₩{profit:,}", f"{profit_rate:.1f}%", delta_color="inverse")
                    
                    # 4. 底部更多信息折叠区
                    with st.expander("🔎 제품 상세 정보 더보기 (查看更多详情)"):
                         st.markdown(f"""
                         - **제품명**: {name}
                         - **쇼핑몰 유형**: {item['mallName']}
                         - **링크**: [Naver Shopping 바로가기]({link})
                         """)
                    
                    st.divider()

        except Exception as e:
            st.error(f"Error: {e}")
