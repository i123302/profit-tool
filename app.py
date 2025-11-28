import streamlit as st
import urllib.request
import json

# === 0. 页面基础设置 ===
st.set_page_config(page_title="Naver 爆款侦察机", page_icon="🕵️", layout="wide")

# === 1. 你的通行证 (API Key) ===
client_id = "D7Y9yz2pKq4U7EgsGhIe"
client_secret = "Uf8RGzI3jJ"

# === 2. 侧边栏 (设置区) ===
with st.sidebar:
    st.header("⚙️ 环境设置")
    exchange_rate = st.number_input("汇率 (1元 = ? 韩币)", value=195)
    shipping_cost = st.number_input("单件运费 (韩币)", value=3000)
    st.divider()
    st.info("💡 提示：Naver API 不直接提供销量/评价数，但我们会通过'店铺类型'帮你判断热度。")

# === 3. 主标题 ===
st.title("🕵️ Naver 选品侦察机 V4.0")
st.markdown("### 🔍 透视竞品：价格 · 利润 · 渠道 · 热度")

# === 4. 搜索输入区 ===
with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("第一步: 输入韩语关键词", placeholder="例如: 기계식 키보드")
    with col2:
        cost_rmb = st.number_input("第二步: 1688进价 (RMB)", value=0)
    with col3:
        st.write("") 
        st.write("") 
        btn_start = st.button("开始侦察 🚀", type="primary", use_container_width=True)

# === 5. 核心分析逻辑 ===
if btn_start:
    if not keyword:
        st.warning("⚠️ 请先输入关键词！")
    else:
        # 计算总成本
        total_cost_krw = (cost_rmb * exchange_rate) + shipping_cost
        
        # 显示成本条
        if cost_rmb > 0:
            st.success(f"📊 **成本红线**: {cost_rmb}元 × {exchange_rate} + 运费 = **{total_cost_krw:,.0f} 韩币**")
        
        st.divider()

        # 调用 API
        encText = urllib.parse.quote(keyword)
        # display=20, sort=sim (按热度/相关度排序，排前面的通常销量好)
        url = "https://openapi.naver.com/v1/search/shop?query=" + encText + "&display=20&sort=sim"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            with st.spinner('正在潜入 Naver 数据库...'):
                response = urllib.request.urlopen(request)
                data = json.loads(response.read().decode('utf-8'))
            
            if not data['items']:
                st.error("❌ 没找到相关商品。")
            else:
                for item in data['items']:
                    # --- 数据清洗 ---
                    name = item['title'].replace('<b>', '').replace('</b>', '')
                    lprice = int(item['lprice']) # 售价
                    hprice = int(item['hprice']) if item['hprice'] else 0 # 原价
                    
                    brand = item.get('brand', '')
                    maker = item.get('maker', '')
                    mall_name = item.get('mallName', '未知店铺')
                    product_type = item.get('productType', '1') # 1=一般, 2=比价聚合
                    
                    category = f"{item['category1']} > {item['category2']} > {item['category3']}"
                    img_url = item['image']
                    link = item['link']

                    # --- 利润计算 ---
                    profit = lprice - total_cost_krw
                    profit_rate = 0
                    if lprice > 0:
                        profit_rate = (profit / lprice) * 100

                    # --- 智能热度判断 (虽然没销量数字，但能推测) ---
                    # 逻辑：如果是'价格比较'链接，说明是全网爆款聚合，销量极高
                    is_hot = False
                    hot_label = ""
                    if product_type == '1' or '가격비교' in link: 
                        is_hot = True
                        hot_label = "🔥 全网比价 (超级爆款)"
                    else:
                        hot_label = f"🏪 {mall_name}"

                    # 过滤超低价配件
                    if cost_rmb > 0 and lprice < (total_cost_krw * 0.4):
                        continue

                    # === 界面展示 ===
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        
                        # 左侧：图片
                        with c1:
                            st.image(img_url, use_container_width=True)
                            if is_hot:
                                st.caption("🔥 流量之王")
                        
                        # 右侧：详情
                        with c2:
                            # 标题
                            st.markdown(f"### [{name}]({link})")
                            
                            # 标签区 (新增：店铺和热度)
                            st.markdown(f"""
                            <span style='background-color:#e8fdf5; padding:4px 8px; border-radius:4px; color:#0d5e42'>**{hot_label}**</span>
                            <span style='background-color:#f0f2f6; padding:4px 8px; border-radius:4px;'>🏷️ 品牌: {brand or '无'}</span> 
                            <span style='background-color:#f0f2f6; padding:4px 8px; border-radius:4px;'>🏭 制造: {maker or 'OEM'}</span>
                            """, unsafe_allow_html=True)
                            
                            st.write("") # 空行

                            # 价格数据区
                            col_p1, col_p2, col_p3 = st.columns(3)
                            with col_p1:
                                st.metric("当前售价", f"₩{lprice:,}")
                            with col_p2:
                                if cost_rmb > 0:
                                    if profit > 0:
                                        st.metric("预估利润", f"₩{profit:,}", f"{profit_rate:.1f}%")
                                    else:
                                        st.metric("预估利润", f"₩{profit:,}", f"{profit_rate:.1f}%", delta_color="inverse")
                                else:
                                    st.metric("进价未填", "-")
                            with col_p3:
                                # 这里虽然没有评论数，但我们做一个按钮引导去查看
                                st.link_button("🔎 去看真实评价", link)
                            
                    st.divider()

        except Exception as e:
            st.error(f"发生错误: {e}")
