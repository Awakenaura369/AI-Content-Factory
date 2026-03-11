import streamlit as st
from groq import Groq
import time

# 1. إعداد الصفحة والعنوان
st.set_page_config(page_title="AI Content Factory 🏭", layout="wide")
st.title("🏭 AI Content Factory - Bulk SEO Articles")
st.write("مرحباً بك أ سي محسن! هاد الأداة مصممة باش 'تحرث' ليك المحتوى بذكاء واحترافية.")

# 2. جلب الـ API Key من Streamlit Secrets
# تأكد انك حاط GROQ_API_KEY فـ Settings ديال الـ App فـ Streamlit Cloud
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("خطأ: الـ API Key ما لقيتوش. تأكد بلي حطيتي GROQ_API_KEY فـ Secrets.")
    st.stop()

# 3. دالة توليد المقالات (معدلة لتفادي الأخطاء)
def generate_seo_article(topic, context):
    try:
        # استعملنا llama-3.1-8b-instant لضمان الاستقرار والسرعة
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional SEO content writer. Write in long-form, using HTML tags for formatting (h2, h3, b, ul, li)."
                },
                {
                    "role": "user",
                    "content": f"Write a 1000-word SEO article about: {topic}. Focus on: {context}. Include a conclusion and FAQ."
                }
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.6,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error occurred: {str(e)}"

# 4. واجهة التحكم (Sidebar)
with st.sidebar:
    st.header("⚙️ إعدادات الحرث")
    main_niche = st.text_input("النيش (مثلاً: Dental AI):", "AI for Dentistry")
    num_to_generate = st.slider("عدد المقالات:", 1, 5, 3)
    st.info("نصيحة: كلما كان النيش دقيق، كلما كان السيو (SEO) قوي.")

# 5. تشغيل عملية الإنتاج
if st.button("ابدأ عملية الإنتاج الضخم! 🔥"):
    st.divider()
    cols = st.columns(1)
    
    for i in range(num_to_generate):
        with st.expander(f"📖 المقال رقم {i+1}", expanded=True):
            with st.spinner(f'جاري كتابة المقال {i+1}...'):
                # تنويع العناوين الفرعية لضمان Uniqueness
                sub_topic = f"Advanced benefits and future of {main_niche} - Part {i+1}"
                content = generate_seo_article(main_niche, sub_topic)
                
                # عرض النتيجة
                st.markdown(content, unsafe_allow_html=True)
                
                # زر للنسخ السريع
                st.code(content, language='html')
                
                st.success(f"المقال {i+1} واجد!")
                time.sleep(2) # راحة للـ API

st.divider()
st.caption("Developed by Mouhcine Digital Systems | Powered by Groq & Llama 3.1")
