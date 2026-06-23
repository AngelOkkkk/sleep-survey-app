import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- 1. Настройка нежно-розового дизайна ---
st.markdown(
    """
    <style>
    /* Основной фон страницы */
    .stApp {
        background-color: #ffe6ea; 
    }
    
    /* Фон боковой панели */
    [data-testid="stSidebar"] {
        background-color: #ffd1dc;
    }
    
    /* Цвет текста для читаемости на розовом фоне */
    .stMarkdown, .stTitle, .stSubheader, label, p, h1, h2, h3 {
        color: #4a4a4a !important;
    }
    
    /* Стилизация кнопок и полей ввода (опционально) */
    .stButton>button {
        background-color: #ffb7c5;
        color: white;
        border: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Инициализация Firebase (Умная версия для Cloud и Локалки) ---
import json # <--- Добавь эту строку в самые верхние импорты, если её там нет!

if not firebase_admin._apps:
    # 1. Пытаемся взять ключ из Secrets (для Streamlit Cloud)
    key_content = os.getenv("FIREBASE_KEY") 
    
    if key_content:
        # Если ключ есть в настройках облака, превращаем текст в объект
        cred_dict = json.loads(key_content)
        cred = credentials.Certificate(cred_dict)
        
    # 2. Если ключа в облаке нет, пытаемся найти файл (для локального запуска)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        
    # 3. Если ничего не нашли — выдаем ошибку
    else:
        st.error("❌ Ошибка: Ключ Firebase не найден ни в Secrets, ни в файле!")
        st.stop()
        
    firebase_admin.initialize_app(cred)

# --- 3. Интерфейс приложения ---
st.set_page_config(page_title="Опрос: Сон и Продуктивность", layout="wide")
st.title("😴 Исследование: Влияние сна на успеваемость")
st.markdown("""
Привет! Этот опрос поможет выяснить, как качество и количество сна влияют на нашу продуктивность.
Все ответы анонимны и используются только для учебной практики.
""")

# Форма с 7 вопросами
with st.form("sleep_survey_form"):
    st.subheader("Блок 1: Режим сна")
    
    # Вопрос 1
    hours_sleep = st.slider(
        "1. Сколько часов вы обычно спите?", 
        min_value=3.0, max_value=12.0, value=7.0, step=0.5
    )
    
    # Вопрос 2
    sleep_quality = st.radio(
        "2. Как вы оцениваете качество своего сна?", 
        options=["Отличное", "Хорошее", "Среднее", "Плохое", "Очень плохое"],
        horizontal=True
    )
    
    # Вопрос 3
    bedtime = st.selectbox(
        "3. Во сколько вы обычно ложитесь спать?", 
        options=["До 22:00", "22:00 - 23:00", "23:00 - 00:00", "00:00 - 01:00", "После 01:00"]
    )
    
    st.divider()
    st.subheader("Блок 2: Привычки и факторы")
    
    # Вопрос 4
    phone_before_bed = st.checkbox("4. Пользуетесь телефоном/гаджетами за 30 минут до сна?")
    
    # Вопрос 5
    caffeine = st.multiselect(
        "5. Что вы употребляете во второй половине дня?", 
        options=["Кофе", "Чай", "Энергетики", "Ничего из перечисленного"]
    )
    
    st.divider()
    st.subheader("Блок 3: Влияние на учебу")
    
    # Вопрос 6
    productivity = st.slider(
        "6. Оцените свою продуктивность днем (1 - низкая, 10 - высокая)", 
        min_value=1, max_value=10, value=5
    )
    
    # Вопрос 7
    gpa_impact = st.multiselect(
        "7. Как недосып влияет на вашу учебу? (можно выбрать несколько)", 
        options=[
            "Сложно концентрироваться на лекциях", 
            "Пропускаю пары / опаздываю", 
            "Снижаются оценки за контрольные", 
            "Нет сил делать домашние задания", 
            "Не замечаю влияния"
        ]
    )
    
    submitted = st.form_submit_button("📤 Отправить ответ", use_container_width=True)

# --- 4. Сохранение данных ---
if submitted:
    record = {
        "hours_sleep": float(hours_sleep),
        "sleep_quality": sleep_quality,
        "bedtime": bedtime,
        "phone_before_bed": bool(phone_before_bed),
        "caffeine": caffeine,
        "productivity": int(productivity),
        "gpa_impact": gpa_impact,
        "timestamp": datetime.utcnow()
    }
    try:
        db.collection("responses").add(record)
        st.success("✅ Спасибо! Ваши данные успешно сохранены в базу.")
        st.balloons()
    except Exception as e:
        st.error(f"Ошибка при сохранении: {e}")

# --- 5. Аналитика ---
if st.checkbox("📊 Показать панель аналитики (для преподавателя)"):
    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]
    
    if data:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        st.subheader("Последние ответы")
        st.dataframe(df.head(10), use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.histogram(
                df, x="hours_sleep", nbins=8, 
                title="Распределение длительности сна",
                color_discrete_sequence=["#ff69b4"]
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            fig2 = px.box(
                df, x="sleep_quality", y="productivity", 
                title="Продуктивность vs Качество сна",
                color="sleep_quality"
            )
            st.plotly_chart(fig2, use_container_width=True)
            
        st.info(f"Всего собрано ответов: {len(df)}")
    else:
        st.warning("Пока нет данных для отображения аналитики.")
