import os
import openai
import streamlit as st
from streamlit_chat import message
from wudao.api_request import getToken, executeEngine


# 简单密码验证
if 'login' not in st.session_state:
    # 根据环境变量“SAMPLE_PASSWORD”是否存在跳过验证
    if 'SAMPLE_PASSWORD' not in os.environ:
        st.session_state['login'] = True
        st._rerun()
    password = st.text_input("输入密码", type="password")
    if password.strip() == os.environ['SAMPLE_PASSWORD']:
        st.session_state['login'] = True
        st._rerun()
    else:
        st.error("密码错误")
        st.stop()

# ------------------ OpenAI ------------------
openai.organization = os.environ["OPENAI_ORG_ID"]
openai.api_key = os.environ['OPENAI_API_KEY']

# ------------------ ZhipuAI ------------------
ZHIPUAI_API_KEY = os.environ["ZHIPUAI_API_KEY"]
ZHIPUAI_PUBLIC_KEY = os.environ['ZHIPUAI_PUBLIC_KEY']
ability_type = "chatGLM"
engine_type = "chatGLM"

# Initialise session state variables
# ------------------ OpenAI ------------------
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

# Setting page title and header
st.set_page_config(page_title="Servyou GPT", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'GPT评估</h1>", unsafe_allow_html=True)

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("设置")
model_name = st.sidebar.radio("模型:", ("智谱","GPT-3.5","GPT-4"))
counter_placeholder = st.sidebar.empty()
# counter_placeholder.write(f"本次会话花费: ${st.session_state['total_cost']:.5f}")

# Map model names to model IDs
if model_name == "智谱":
    model = "chatGLM"
elif model_name == "GPT-3.5":
    model = "gpt-3.5-turbo"
else:
    model = "gpt-4"


def generate_response(prompt):
    if model_name == "智谱":
        return generate_response_zhipuai(prompt)
    else:
        return generate_response_openai(prompt)

def generate_response_openai(prompt):

    st.session_state['messages'].append({"role": "user", "content": prompt})

    completion = openai.ChatCompletion.create(
        model=model,
        messages=st.session_state['messages']
    )
    response = completion.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": response})

    # print(st.session_state['messages'])
    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

def generate_response_zhipuai(prompt):
    data = {
        "top_p": 0.7,
        "temperature": 0.9,
        "prompt": prompt,
        "requestTaskNo": "1542097269879345154",
        "history": []
    }
    if 'zhipu_token' not in st.session_state:
        token_result = getToken(ZHIPUAI_API_KEY, ZHIPUAI_PUBLIC_KEY)
        if not token_result:
            response = "error getToken()"
            return response
        code = token_result["code"]
        if code != 200:
            response = "error:"+code+":获取 token 失败，请检查 API_KEY 和 PUBLIC_KEY"
            return response
        st.session_state['zhipu_token'] = token_result["data"]
    zhipu_token = st.session_state['zhipu_token']
    resp = executeEngine(ability_type, engine_type, zhipu_token, data)
    if resp["code"] != 200:
        response = "error:"+resp["code"]+":执行引擎失败"
        return response

    response = resp["data"]["outputText"]
    st.session_state['messages'].append({"role": "assistant", "content": response})

    # print(st.session_state['messages'])
    # TODO: get total_tokens, prompt_tokens, completion_tokens
    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    return response, total_tokens, prompt_tokens, completion_tokens


# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("问:", key='input', height=100)
        submit_button = st.form_submit_button(label='发送')

    if submit_button and user_input:
        output, total_tokens, prompt_tokens, completion_tokens = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)
        st.session_state['model_name'].append(model_name)
        st.session_state['total_tokens'].append(total_tokens)

        # from https://openai.com/pricing#language-models
        if model_name == "GPT-3.5":#TODO
            cost = total_tokens * 0.002 / 1000
        else:
            cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000

        st.session_state['cost'].append(cost)
        st.session_state['total_cost'] += cost
clear_button = st.button("重置会话（可以节省花费）", key="clear")
# reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []

st.write(f"本次会话花费: ${st.session_state['total_cost']:.5f}")

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
            st.write(
                f"上述由 {st.session_state['model_name'][i]} 回答;  花费: {st.session_state['total_tokens'][i]}个令牌、{st.session_state['cost'][i]:.5f}$")

            #counter_placeholder.write(f"本次会话共花费: ${st.session_state['total_cost']:.5f}")
