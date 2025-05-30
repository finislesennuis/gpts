import streamlit as st
import google.generativeai as genai
from typing import List, Dict, Any

# 페이지 설정
st.set_page_config(
    page_title="나만의 프롬프트 기반 Gemini 챗봇",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded"  # 사이드바를 기본적으로 펼친 상태로 설정
)

# 세션 상태 초기화
if "role_prompt" not in st.session_state:
    st.session_state.role_prompt = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# Gemini API 설정
def initialize_gemini() -> genai.GenerativeModel:
    """Gemini API와 모델을 초기화합니다."""
    try:
        # API 키 검증
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ API 키가 설정되지 않았습니다.")
            st.stop()
        
        # API 설정
        genai.configure(api_key=api_key)
        
        # 모델 초기화
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "top_p": 1,
                "top_k": 32
            }
        )
    except Exception as e:
        st.error("❌ Gemini 모델을 초기화할 수 없습니다.")
        st.stop()

# 프롬프트 생성 함수
def create_prompt(role_prompt: str, messages: List[Dict[str, str]]) -> str:
    """
    AI에게 전달할 프롬프트를 생성합니다.
    
    Args:
        role_prompt: 설정된 역할 프롬프트
        messages: 이전 대화 내역
    
    Returns:
        str: 구성된 프롬프트
    """
    # 1. 역할 프롬프트
    prompt = f"당신은 {role_prompt} 역할을 맡고 있습니다.\n\n"
    
    # 2. 대화 내역 추가
    if messages:
        prompt += "지금까지의 대화 내역:\n"
        for msg in messages:
            role = "사용자" if msg["role"] == "user" else "AI"
            prompt += f"{role}: {msg['content']}\n"
    
    # 3. 마지막에 AI: 추가
    prompt += "\nAI:"
    
    return prompt

# Gemini 모델 초기화
model = initialize_gemini()

# 사이드바 설정
with st.sidebar:
    st.title("⚙️ 챗봇 설정")
    st.markdown("---")
    
    # 역할 프롬프트 입력
    st.subheader("🎭 역할 설정")
    role_prompt = st.text_area(
        "챗봇의 역할을 설정해주세요",
        placeholder="예시: 넌 여행 전문가야. 세계 각국의 여행 정보와 팁을 제공해줘.",
        height=150,
        help="챗봇이 맡을 역할을 자세히 설명해주세요. 역할에 따라 챗봇의 응답이 달라집니다."
    )
    
    # 프롬프트 적용 버튼
    if st.button("✨ 프롬프트 적용", type="primary", use_container_width=True):
        if role_prompt.strip():
            # 세션 상태 업데이트
            st.session_state.role_prompt = role_prompt.strip()
            # 대화 기록 초기화
            st.session_state.messages = []
            st.success("✅ 역할이 성공적으로 설정되었습니다!")
            st.rerun()  # 역할 변경 후 UI 새로고침
        else:
            st.error("❌ 역할 프롬프트를 입력해주세요.")
    
    st.markdown("---")
    st.markdown("### 💡 역할 설정 예시")
    st.markdown("""
    - 넌 여행 전문가야. 세계 각국의 여행 정보와 팁을 제공해줘.
    - 넌 친절한 영어 선생님이야. 영어 학습에 대한 조언을 해줘.
    - 넌 요리 전문가야. 다양한 요리 레시피와 요리 팁을 알려줘.
    - 넌 프로그래밍 멘토야. 코딩 관련 질문에 답변해줘.
    """)

# 메인 영역
st.title("🧠 나만의 프롬프트 기반 Gemini 챗봇")
st.markdown("이 챗봇은 사용자가 정한 역할에 따라 문맥을 기억하고 대화합니다.")

# 현재 역할 상태 표시
if not st.session_state.role_prompt:
    st.warning("⚠️ 챗봇의 역할이 설정되지 않았습니다. 왼쪽 사이드바에서 역할을 설정해주세요.")
    st.stop()
else:
    st.info(f"📝 현재 역할: {st.session_state.role_prompt}")

# 채팅 인터페이스
st.divider()
st.subheader("💬 대화")

# 이전 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # AI 응답 생성
    try:
        # 프롬프트 생성
        full_prompt = create_prompt(st.session_state.role_prompt, st.session_state.messages)
        
        # AI 응답 생성
        response = model.generate_content(
            full_prompt,
            stream=True
        )
        
        # 응답 표시
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # 스트리밍 응답 처리
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        message_placeholder.write(full_response + "▌")
                
                # 최종 응답 표시
                message_placeholder.write(full_response)
                
                # 대화 기록에 AI 응답 추가
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                # 스트리밍 중 오류 발생 시
                error_msg = "❌ 답변 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                message_placeholder.write(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
    except Exception as e:
        # 응답 생성 중 오류 발생 시
        error_msg = "❌ 답변 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        with st.chat_message("assistant"):
            st.write(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg}) 
