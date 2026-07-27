# pages/Login.py
import sys
from pathlib import Path

# إضافة المسار الصحيح للمشروع
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(
    page_title="ByToBy Pro - تسجيل الدخول",
    page_icon="🔐",
    layout="centered"
)

# ============================================
# إدارة المستخدمين
# ============================================

def init_session_state():
    """تهيئة حالة الجلسة"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'مستخدم'
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

init_session_state()

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """تحميل بيانات المستخدمين"""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # إنشاء مستخدم افتراضي
        default_users = {
            "admin": {
                "password": hash_password("admin123"),
                "role": "مدير",
                "email": "admin@bytoby.com",
                "created_at": datetime.now().isoformat()
            },
            "user": {
                "password": hash_password("user123"),
                "role": "مستخدم",
                "email": "user@bytoby.com",
                "created_at": datetime.now().isoformat()
            }
        }
        save_users(default_users)
        return default_users

def save_users(users):
    """حفظ بيانات المستخدمين"""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

def authenticate(username, password):
    """التحقق من صحة المستخدم"""
    users = load_users()
    if username in users:
        if users[username]["password"] == hash_password(password):
            return True, users[username]
    return False, None

def create_user(username, password, email, role="مستخدم"):
    """إنشاء مستخدم جديد"""
    users = load_users()
    if username in users:
        return False, "اسم المستخدم موجود بالفعل"
    
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "email": email,
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    return True, "تم إنشاء المستخدم بنجاح"

# ============================================
# واجهة المستخدم
# ============================================

def login_page():
    """صفحة تسجيل الدخول"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(145deg, #1e1e1e, #2d2d2d);
            border-radius: 20px;
            border: 1px solid #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .login-title {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-title h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #00ff88, #00bfff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-title p {
            color: #aaa;
            font-size: 1rem;
        }
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #00ff88, #00bfff);
            color: black;
            font-weight: bold;
            border: none;
            padding: 0.75rem;
            border-radius: 10px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(0,255,136,0.3);
        }
        .guest-btn {
            text-align: center;
            margin-top: 1rem;
        }
        .guest-btn > button {
            background: transparent;
            border: 1px solid #555;
            color: #aaa;
        }
        .guest-btn > button:hover {
            border-color: #00ff88;
            color: #00ff88;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="login-container">
                <div class="login-title">
                    <h1>🤖 ByToBy Pro</h1>
                    <p>تسجيل الدخول إلى منصة التداول الذكية</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # اختيار وضع الدخول
            login_mode = st.radio(
                "اختر طريقة الدخول",
                ["تسجيل الدخول", "إنشاء حساب جديد"],
                horizontal=True
            )

            if login_mode == "تسجيل الدخول":
                with st.form("login_form"):
                    username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
                    password = st.text_input("🔑 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("🚀 تسجيل الدخول", use_container_width=True)
                    with col2:
                        guest = st.form_submit_button("👤 دخول كضيف", use_container_width=True)

                    if submitted:
                        if username and password:
                            success, user_data = authenticate(username, password)
                            if success:
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_role = user_data.get('role', 'مستخدم')
                                st.session_state.user_email = user_data.get('email', '')
                                st.success(f"✅ مرحباً {username}!")
                                st.rerun()
                            else:
                                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
                        else:
                            st.warning("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور")

                    if guest:
                        # دخول كضيف
                        st.session_state.logged_in = True
                        st.session_state.username = "ضيف"
                        st.session_state.user_role = "ضيف"
                        st.session_state.user_email = ""
                        st.success("✅ تم الدخول كضيف")
                        st.rerun()

                # معلومات الحسابات الافتراضية
                with st.expander("ℹ️ حسابات تجريبية"):
                    st.markdown("""
                    **حساب المدير:**
                    - المستخدم: `admin`
                    - كلمة المرور: `admin123`
                    
                    **حساب المستخدم:**
                    - المستخدم: `user`
                    - كلمة المرور: `user123`
                    """)

            else:  # إنشاء حساب جديد
                with st.form("register_form"):
                    new_username = st.text_input("👤 اسم المستخدم", placeholder="اختر اسم مستخدم")
                    new_password = st.text_input("🔑 كلمة المرور", type="password", placeholder="اختر كلمة مرور قوية")
                    confirm_password = st.text_input("✅ تأكيد كلمة المرور", type="password", placeholder="أعد كتابة كلمة المرور")
                    new_email = st.text_input("📧 البريد الإلكتروني", placeholder="example@email.com")
                    
                    submitted = st.form_submit_button("📝 إنشاء حساب", use_container_width=True)

                    if submitted:
                        if not new_username or not new_password or not new_email:
                            st.warning("⚠️ يرجى ملء جميع الحقول")
                        elif new_password != confirm_password:
                            st.error("❌ كلمة المرور غير متطابقة")
                        elif len(new_password) < 6:
                            st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                        else:
                            success, message = create_user(new_username, new_password, new_email)
                            if success:
                                st.success(f"✅ {message}")
                                st.info("📝 يمكنك الآن تسجيل الدخول بحسابك الجديد")
                            else:
                                st.error(f"❌ {message}")

    # Footer
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem; font-size: 0.8rem;">
        ByToBy Pro v1.0.0 &copy; 2026 - جميع الحقوق محفوظة
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    login_page()
