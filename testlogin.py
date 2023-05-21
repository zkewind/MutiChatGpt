import streamlit as st
# 定义密码
password = "123456"
# 判断是否已经验证通过
if "authenticated" not in st.session_state:
    # 显示密码输入框
    user_input = st.text_input("请输入密码", type="password")
    if user_input == password:
        # 核对密码通过
        st.session_state["authenticated"] = True
        st._rerun()
        st.warning("验证通过！请刷新页面查看主页。")
    else:
        st.warning("密码错误，请重新输入！")
else:
    # 验证已经通过，显示主页内容
    st.write("欢迎访问主页！")