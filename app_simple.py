import streamlit as st
import cv2
import numpy as np
import json
import time
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import os

# 页面配置
st.set_page_config(
    page_title="Python自动考试系统",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'face_verified' not in st.session_state:
    st.session_state.face_verified = False
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'exam_started' not in st.session_state:
    st.session_state.exam_started = False
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

# 加载题库
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("题库文件未找到，请联系管理员")
        return []

# 验证学号格式
def validate_student_id(student_id):
    if len(student_id) == 11 and student_id.startswith('20241315') and student_id[8:].isdigit():
        return True
    return False

# 简化的人脸检测（使用OpenCV的Haar级联）
def detect_face_simple(image):
    # 转换为灰度图
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # 使用OpenCV内置的人脸检测器
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    return len(faces) > 0

# 用户登录
def login_page():
    st.title("🎓 Python自动考试系统")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("学生登录")
        
        with st.form("login_form"):
            student_id = st.text_input("学号", placeholder="请输入学号 (格式: 20241315XXX)")
            password = st.text_input("密码", type="password", placeholder="密码与学号相同")
            
            submitted = st.form_submit_button("登录", use_container_width=True)
            
            if submitted:
                if not validate_student_id(student_id):
                    st.error("学号格式错误！请输入正确的学号格式：20241315XXX")
                elif student_id != password:
                    st.error("密码错误！密码应与学号相同")
                else:
                    st.session_state.logged_in = True
                    st.session_state.student_id = student_id
                    st.success("登录成功！")
                    st.rerun()

# 人脸识别页面（简化版）
def face_recognition_page():
    st.title("🔐 身份验证")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader(f"学号：{st.session_state.student_id}")
        st.info("请点击下方按钮进行人脸识别验证")
        
        # 摄像头捕获
        camera_input = st.camera_input("请对准摄像头进行人脸识别")
        
        if camera_input is not None:
            # 处理图像
            image = Image.open(camera_input)
            
            # 简化的人脸检测
            try:
                has_face = detect_face_simple(image)
                
                if has_face:
                    st.success("✅ 人脸识别成功！")
                    if st.button("开始考试", use_container_width=True):
                        st.session_state.face_verified = True
                        st.session_state.exam_started = True
                        st.session_state.start_time = datetime.now()
                        st.rerun()
                else:
                    st.warning("⚠️ 未检测到人脸，请重新拍照")
            except Exception as e:
                st.warning("⚠️ 人脸检测遇到问题，但您可以继续考试")
                if st.button("继续考试", use_container_width=True):
                    st.session_state.face_verified = True
                    st.session_state.exam_started = True
                    st.session_state.start_time = datetime.now()
                    st.rerun()
        
        if st.button("返回登录", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# 考试页面
def exam_page():
    questions = load_questions()
    if not questions:
        return
    
    st.title("📝 Python知识考试")
    
    # 显示考试信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"学号：{st.session_state.student_id}")
    with col2:
        if st.session_state.start_time:
            elapsed = datetime.now() - st.session_state.start_time
            st.info(f"已用时间：{str(elapsed).split('.')[0]}")
    with col3:
        st.info(f"题目总数：{len(questions)}")
    
    st.markdown("---")
    
    # 显示题目
    with st.form("exam_form"):
        for i, question in enumerate(questions):
            st.subheader(f"第 {i+1} 题")
            st.write(question['question'])
            
            answer = st.radio(
                f"请选择答案：",
                options=question['options'],
                key=f"q_{i}",
                index=None
            )
            
            if answer:
                st.session_state.answers[i] = answer
            
            st.markdown("---")
        
        submitted = st.form_submit_button("提交考试", use_container_width=True)
        
        if submitted:
            if len(st.session_state.answers) == 0:
                st.error("请至少完成一道题目后再提交！")
            else:
                # 显示提交确认信息
                unanswered_count = len(questions) - len(st.session_state.answers)
                if unanswered_count > 0:
                    st.warning(f"⚠️ 您还有 {unanswered_count} 题未答，未答题目将按错误计算。")
                    st.info(f"✅ 已完成 {len(st.session_state.answers)}/{len(questions)} 题")
                else:
                    st.success("✅ 所有题目已完成！")
                
                calculate_score(questions)

# 计算分数
def calculate_score(questions):
    correct_count = 0
    total_questions = len(questions)
    
    for i, question in enumerate(questions):
        if i in st.session_state.answers:
            if st.session_state.answers[i] == question['correct_answer']:
                correct_count += 1
    
    score = (correct_count / total_questions) * 100
    
    # 保存成绩
    save_result(score, correct_count, total_questions)
    
    # 显示结果
    show_result(score, correct_count, total_questions)

# 保存考试结果
def save_result(score, correct_count, total_questions):
    result = {
        'student_id': st.session_state.student_id,
        'score': score,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'exam_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'duration': str(datetime.now() - st.session_state.start_time).split('.')[0]
    }
    
    # 保存到文件
    results_file = 'exam_results.json'
    if os.path.exists(results_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = []
    
    results.append(result)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

# 显示考试结果
def show_result(score, correct_count, total_questions):
    st.balloons()
    
    st.title("🎉 考试完成")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("考试成绩")
        
        # 成绩显示
        if score >= 90:
            st.success(f"🏆 优秀！得分：{score:.1f}分")
        elif score >= 80:
            st.success(f"👍 良好！得分：{score:.1f}分")
        elif score >= 70:
            st.warning(f"📚 中等！得分：{score:.1f}分")
        elif score >= 60:
            st.warning(f"⚠️ 及格！得分：{score:.1f}分")
        else:
            st.error(f"❌ 不及格！得分：{score:.1f}分")
        
        st.info(f"正确题数：{correct_count}/{total_questions}")
        st.info(f"考试时长：{str(datetime.now() - st.session_state.start_time).split('.')[0]}")
        
        if st.button("重新考试", use_container_width=True):
            # 重置状态
            st.session_state.exam_started = False
            st.session_state.face_verified = False
            st.session_state.answers = {}
            st.session_state.start_time = None
            st.rerun()
        
        if st.button("退出系统", use_container_width=True):
            # 完全重置
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# 主程序
def main():
    # 添加CSS样式
    st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 路由逻辑
    if not st.session_state.logged_in:
        login_page()
    elif not st.session_state.face_verified:
        face_recognition_page()
    elif st.session_state.exam_started:
        exam_page()

if __name__ == "__main__":
    main()