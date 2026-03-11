import streamlit as st
from groq import Groq
import time

# إعداد واجهة Streamlit
st.set_page_config(page_title="AI Content Factory 🚀", layout="wide")
st.title("🏭 AI Content Factory - Bulk SEO Articles")
st.write("ولد البادية كايحرث المحتوى بالذكاء الاصطناعي!")

# السكريت (Secret API Key)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def generate_bulk_article(topic, subtopic):
    prompt = f"""
    Write a professional, long-form SEO blog post about: {topic} - Specifically: {subtopic}.
    Requirements:
    - Language: English.
    - Format: HTML (use <h2>, <h3>, <ul>, <li>, <b>).
    - Content: Minimum 800 words, include an FAQ section at the end.
    - SEO: High keyword density for '{topic}'.
    - Tone: Informative and human-like.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-70b-versatile",
        temperature=0.6,
    )
    return chat_completion.choices[0].message.content

# المدخلات
with st.sidebar:
    st.header("⚙️ Settings")
    main_topic = st.text_input("الموضوع الأساسي (Main Niche):", "AI for Dentistry")
    num_articles = st.number_input("عدد المقالات:", min_value=1, max_value=10, value=3)
    
if st.button("ابدأ عملية الحرث! 🚜"):
    st.info(f"جاري توليد {num_articles} مقالات احترافية...")
    
    for i in range(num_articles):
        with st.expander(f"المقال رقم {i+1}"):
            with st.spinner('جاري الكتابة...'):
                # توليد عنوان فرعي مختلف لكل مقال
                article_content = generate_bulk_article(main_topic, f"Aspect {i+1} of {main_topic}")
                st.code(article_content, language='html')
                st.success(f"تم إنتاج المقال {i+1} بنجاح!")
                time.sleep(1) # لتفادي ضغط الـ API
