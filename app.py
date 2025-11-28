import streamlit as st
import urllib.request
import json
import pandas as pd

# === 页面配置 ===
st.set_page_config(page_title="Boss Selection Tool", page_icon="🔐", layout="wide")

# === 🔐 第一步：安全验证 (只有输入密码才能用) ===
# 默认密码是 8888 (你可以自己在下面改)
PASSWORD = "8888" 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.password_input == PASSWORD:
        st.session_state.authenticated = True
    else:
        st.error("🚫 암호가 틀렸습니다 (密码错误)")

if not st.session_state.authenticated:
    st.markdown("### 🔒 VIP Access Only")
    st.text_input("비밀번호를 입력하세요 (请输入访问密码):", type="password", key="password_input", on_change=check_password)
    st.stop() # 密码不对，下面的代码都不执行

# ==========================================
# 🔓 密码正确，显示以下内容 (真正的工具界面)
# ==========================================

# === API 设置 ===
client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 侧边栏：精准成本控制 ===
with st.sidebar:
    st.header("💰 정밀 마진 계산 (精准利润设置)")
    
    # 基础设置
    exchange_rate = st.number_input("환율 (1 RMB = ? KRW)", value=195)
    shipping_cost = st.number_input("건당 배송비 (运费 KRW)", value=3000)
    
    st.divider()
    
    # ⚠️ 新增：隐形成本
    platform_fee = st.slider("플랫폼 수수료 (平台手续费 %)", 0.0, 15.0, 5.5, format="%.1f%%")
    vat_tax = st.slider("부가세 (VAT 税率 %)", 0.0, 20.0, 10.0, format="%.1f%%")
    
    st.info(f"💡 현재 설정: 수수료 {platform_fee}% + 부가세 {vat_tax}% 차감 후 순이익을 계산합니다.")

# === 主标题 ===
st.title("🔐 사장님 전용 소싱 분석기 (V8.0)")
st.markdown("### 📊 순수익(Net Profit) 정밀 분석")

# === 搜索区 ===
with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("검색어 (Keyword)", placeholder="예: 로지텍 마우스")
    with col2:
        cost_rmb = st.number_input("소싱 원가 (RMB)", value=0)
    with col3:
        st.write("") 
        st.write("") 
        btn_start = st.button("정밀 분석 시작 🚀", type="primary", use_container_width=True)

# === 核心逻辑 ===
if btn_start:
    if not keyword:
        st.warning("⚠️ 키워드를 입력해주세요!")
    else:
        # 1. 基础成本 (进货+运费)
        base_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        
        # 显示成本结构
        if cost_rmb > 0:
            st.success(f"""
            🧾 **비용 구조 분석**:
            - 제품원가 + 배송비: {base_cost_krw:,.0f} 원
            - (판매가에 따라 수수료 {platform_fee}% + 부가세 {vat_tax}%가 추가로 차감됩니다)
            """)
        st.divider()

        # 2. 调用 API
        encText = urllib.parse.quote(keyword)
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=30&sort=sim"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('정밀 계산 중...'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            if not data['items']:
                st.error("❌ 데이터가 없습니다.")
            else:
                excel_data = [] 

                for item in data['items']:
                    name = item['title'].replace('<b>', '').replace('</b>', '')
                    lprice = int(item['lprice']) # 售价
                    mall_name = item['mallName']
                    link = item['link']
                    img_url = item['image']
                    
                    # === 💰 核心升级：真·净利润计算公式 ===
                    # 平台费 = 售价 * 费率
                    fee_cost = lprice * (platform_fee / 100)
                    # 税费 = 售价 * 税率 (简单估算)
                    tax_cost = lprice * (vat_tax / 100)
                    
                    # 总扣除
                    total_deduction = base_cost_krw + fee_cost + tax_cost
                    
                    # 净利润
                    net_profit = lprice - total_deduction
                    net_profit_rate = (net_profit / lprice) * 100 if lprice > 0 else 0
                    
                    # 准备导出数据
                    excel_data.append({
                        "상품명": name,
                        "판매가": lprice,
                        "순수익 (Net Profit)": round(net_profit),
                        "마진율 (%)": f"{net_profit_rate:.1f}%",
                        "플랫폼 수수료": round(fee_cost),
                        "부가세(Est)": round(tax_cost),
                        "쇼핑몰": mall_name,
                        "링크": link
                    })

                    # 过滤逻辑 (只显示还行的)
                    if cost_rmb > 0 and net_profit < 0:
                        # 如果亏本，标记一下，但还是显示，方便避坑
                        pass

                    # === 界面展示 ===
                    with st.container():
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            st.image(img_url, use_container_width=True)
                            if '쿠팡' in mall_name:
                                st.caption("🚀 Coupang")
                        
                        with c2:
                            st.markdown(f"**[{name}]({link})**")
                            st.caption(f"🏪 {mall_name}")
                            
                            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                            with col_p1:
                                st.metric("판매가", f"₩{lprice:,}")
                            with col_p2:
                                st.metric("수수료+세금 (Est)", f"-₩{int(fee_cost+tax_cost):,}")
                            with col_p3:
                                if cost_rmb > 0:
                                    # 颜色逻辑：赚钱是正常色，亏钱是反色
                                    if net_profit > 0:
                                        st.metric("순수익 (净赚)", f"₩{int(net_profit):,}", f"{net_profit_rate:.1f}%")
                                    else:
                                        st.metric("순수익 (亏损)", f"₩{int(net_profit):,}", f"{net_profit_rate:.1f}%", delta_color="inverse")
                                else:
                                    st.metric("원가 미입력", "-")
                            with col_p4:
                                st.link_button("👉 구매 페이지", link)
                        
                        st.divider()

                # === 导出按钮 ===
                if excel_data:
                    df = pd.DataFrame(excel_data)
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.sidebar.download_button(
                        label="📥 엑셀(CSV) 다운로드",
                        data=csv,
                        file_name='net_profit_analysis.csv',
                        mime='text/csv',
                        type='primary'
                    )

        except Exception as e:
            st.error(f"Error: {e}")
