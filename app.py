import streamlit as st
import urllib.request
import json
import pandas as pd

# 页面设置
st.set_page_config(page_title="中韩选品利润计算器", page_icon="💰")

# === 你的通行证 ===
client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 侧边栏 ===
with st.sidebar:
    st.header("⚙️ 参数设置")
    exchange_rate = st.number_input("汇率 (RMB -> KRW)", value=195)
    shipping_cost = st.number_input("单件运费 (KRW)", value=3000)
    st.info("💡 提示: 运费包含国际物流+韩国派送费")

# === 主界面 ===
st.title("🚀 韩国电商利润挖掘机")
st.markdown("输入 **关键词** 和 **1688进货价**，AI 自动帮你算利润。")

col1, col2 = st.columns([2, 1])
with col1:
    keyword = st.text_input("🔍 搜索关键词 (韩语)", placeholder="例如: AULA F87")
with col2:
    cost_rmb = st.number_input("📦 进货价 (RMB)", value=0)

if st.button("开始分析 🔥", type="primary", use_container_width=True):
    if not keyword or cost_rmb == 0:
        st.warning("⚠️ 请输入关键词和进货价！")
    else:
        # === 核心逻辑 ===
        total_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        st.success(f"📊 成本估算: {cost_rmb} RMB ≈ **{total_cost_krw:,.0f}** 韩币 (含运费)")
        
        # 调用 Naver API
        encText = urllib.parse.quote(keyword)
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=10&sort=sim"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('正在连接 Naver 数据库...'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            # 没找到商品
            if not data['items']:
                st.error("❌ 没找到相关商品，请换个词试试。")
            else:
                st.markdown("### 🇰🇷 市场行情分析")
                for item in data['items']:
                    name = item['title'].replace('<b>', '').replace('</b>', '')
                    sell_price = int(item['lprice'])
                    profit = sell_price - total_cost_krw
                    profit_rate = (profit / sell_price) * 100
                    
                    # 卡片展示
                    with st.container():
                        c1, c2, c3 = st.columns([3, 1, 1])
                        with c1:
                            st.markdown(f"**[{name}]({item['link']})**")
                        with c2:
                            st.metric("Naver售价", f"₩{sell_price:,}")
                        with c3:
                            if profit > 0:
                                st.metric("预计利润", f"₩{profit:,}", f"{profit_rate:.1f}%")
                            else:
                                st.metric("预计利润", f"₩{profit:,}", f"{profit_rate:.1f}%", delta_color="inverse")
                    st.divider()
                
        except Exception as e:
            st.error(f"出错了: {e}")
