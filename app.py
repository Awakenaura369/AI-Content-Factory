import streamlit as st
from groq import Groq
import time
import zipfile
import io
import re
import requests
from datetime import datetime

# ============================================================
# 1. إعداد الصفحة
# ============================================================
st.set_page_config(
    page_title="AI Content Factory 🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص لواجهة أحسن
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #e94560;
    }
    .main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
    .main-header p  { color: #a8b2d8; margin: 0.5rem 0 0; font-size: 1.1rem; }

    .stat-card {
        background: #16213e;
        border: 1px solid #0f3460;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-card .number { font-size: 2rem; font-weight: 700; color: #e94560; }
    .stat-card .label  { color: #a8b2d8; font-size: 0.85rem; }

    .article-container {
        background: #1a1a2e;
        border: 1px solid #0f3460;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .article-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #0f3460;
    }
    .badge {
        background: #e94560;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .stButton > button {
        background: linear-gradient(135deg, #e94560, #c62a47) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(233,69,96,0.4) !important;
    }

    .keyword-tag {
        display: inline-block;
        background: #0f3460;
        color: #a8b2d8;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    .success-banner {
        background: linear-gradient(135deg, #0d7377, #14a085);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. جلب الـ API Key
# ============================================================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("⚠️ خطأ: الـ API Key ما لقيتوش. تأكد بلي حطيتي GROQ_API_KEY فـ Secrets.")
    st.stop()

# Unsplash API (اختياري)
UNSPLASH_KEY = st.secrets.get("UNSPLASH_ACCESS_KEY", "")

# ============================================================
# 3. Header
# ============================================================
st.markdown("""
<div class="main-header">
    <h1>🏭 AI Content Factory</h1>
    <p>مصنع المحتوى الذكي — اكتب، حسّن، وصدّر بضغطة زر</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 4. Session State
# ============================================================
if "generated_articles" not in st.session_state:
    st.session_state.generated_articles = []
if "total_words" not in st.session_state:
    st.session_state.total_words = 0

# ============================================================
# 5. Sidebar — إعدادات متقدمة
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ إعدادات الإنتاج")

    # --- النيش والكلمات المفتاحية ---
    st.markdown("### 🎯 الموضوع والكلمات المفتاحية")
    main_niche = st.text_input("النيش الرئيسي:", "AI for Dentistry")
    keywords_input = st.text_area(
        "كلمات مفتاحية (واحدة فكل سطر):",
        "dental AI software\nteeth whitening AI\nbest dental tools 2025",
        height=100,
        help="كل كلمة فسطر. غادي يتضمنوها فالمقالات."
    )
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]

    st.markdown("---")

    # --- اللغة ---
    st.markdown("### 🌍 اللغة")
    language = st.selectbox(
        "لغة المقال:",
        ["English", "العربية", "Français", "Español", "Deutsch"],
        index=0
    )

    st.markdown("---")

    # --- إعدادات المقال ---
    st.markdown("### 📝 إعدادات المقال")
    num_to_generate = st.slider("عدد المقالات:", 1, 10, 3)
    article_length = st.select_slider(
        "طول المقال:",
        options=["500 كلمة", "800 كلمة", "1000 كلمة", "1500 كلمة", "2000 كلمة"],
        value="1000 كلمة"
    )
    article_tone = st.selectbox(
        "أسلوب الكتابة:",
        ["Professional", "Conversational", "Educational", "Persuasive", "Neutral"],
        index=0
    )
    include_faq = st.checkbox("✅ إضافة FAQ", value=True)
    include_conclusion = st.checkbox("✅ إضافة خاتمة", value=True)
    include_meta = st.checkbox("✅ توليد Meta Description", value=True)

    st.markdown("---")

    # --- النموذج ---
    st.markdown("### 🤖 النموذج")
    model_choice = st.selectbox(
        "اختر النموذج:",
        [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
        ],
        index=0,
        help="النماذج الأقوى تعطي جودة أحسن لكن أبطأ شوية."
    )
    temperature = st.slider("الإبداع (Temperature):", 0.1, 1.0, 0.6, 0.1)

    st.markdown("---")

    # --- Unsplash ---
    st.markdown("### 🖼️ الصورة التمثيلية")
    include_image = st.checkbox("✅ إضافة صورة من Unsplash", value=True)
    image_position = st.selectbox(
        "موضع الصورة:",
        ["بعد العنوان مباشرة", "في المنتصف", "في الأخير"],
        disabled=not include_image,
    )
    if include_image and not UNSPLASH_KEY:
        st.warning("⚠️ حط UNSPLASH_ACCESS_KEY فـ Secrets باش تشتغل هاد الميزة.")

    st.markdown("---")
    st.info("💡 نصيحة: زيد الكلمات المفتاحية باش يتحسن الـ SEO.")

# ============================================================
# 6. دالة بناء الـ Prompt
# ============================================================
def build_prompt(topic, keywords, language, length, tone, faq, conclusion, meta, part_num):
    word_count = length.split(" ")[0]
    kw_str = ", ".join(keywords[:5]) if keywords else topic

    lang_instruction = {
        "English": "Write in English.",
        "العربية": "اكتب باللغة العربية الفصحى.",
        "Français": "Écris en français.",
        "Español": "Escribe en español.",
        "Deutsch": "Schreibe auf Deutsch.",
    }.get(language, "Write in English.")

    extras = []
    if faq:        extras.append("Include a FAQ section with 5 questions and answers.")
    if conclusion: extras.append("Include a strong conclusion.")
    if meta:       extras.append("At the very end, add a line: META: [your meta description here] (max 160 chars).")

    subtopics = [
        f"benefits and ROI of {topic}",
        f"how to implement {topic} step by step",
        f"future trends in {topic}",
        f"common mistakes to avoid with {topic}",
        f"case studies and real examples of {topic}",
        f"comparing top tools for {topic}",
        f"beginners guide to {topic}",
        f"advanced strategies for {topic}",
        f"cost analysis of {topic}",
        f"expert tips for mastering {topic}",
    ]
    subtopic = subtopics[(part_num - 1) % len(subtopics)]

    return f"""
You are an expert SEO content writer. {lang_instruction}

Write a {word_count}-word SEO-optimized article about: "{topic}"
Subtopic focus: {subtopic}
Target keywords (use naturally throughout): {kw_str}
Tone: {tone}

Formatting requirements:
- Use HTML tags: <h2>, <h3>, <b>, <ul>, <li>, <p>
- Start with an engaging introduction (no h1 tag)
- Use keyword-rich subheadings
- Write in short, scannable paragraphs
{chr(10).join(f'- {e}' for e in extras)}

Make the article unique, valuable, and fully optimized for search engines.
""".strip()

# ============================================================
# 7.5 دوال Unsplash
# ============================================================
def fetch_unsplash_image(query):
    """تجيب صورة من Unsplash مرتبطة بالموضوع"""
    if not UNSPLASH_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.unsplash.com/photos/random",
            params={"query": query, "orientation": "landscape", "content_filter": "high"},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "url":          data["urls"]["regular"],          # رابط الصورة
                "thumb":        data["urls"]["small"],            # thumbnail للمعاينة
                "alt":          data["alt_description"] or query, # النص البديل
                "photographer": data["user"]["name"],             # اسم المصور
                "profile":      data["user"]["links"]["html"],    # رابط المصور
                "unsplash_url": data["links"]["html"],            # رابط الصورة على Unsplash
            }
    except Exception:
        pass
    return None


def build_image_html(img_data, topic):
    """تبني HTML احترافي للصورة مع attribution كما تطلب Unsplash"""
    if not img_data:
        return ""
    return f"""
<figure style="margin:2rem 0;text-align:center;">
  <img
    src="{img_data['url']}"
    alt="{img_data['alt']}"
    title="{topic}"
    style="max-width:100%;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.15);"
    loading="lazy"
  />
  <figcaption style="font-size:0.8rem;color:#888;margin-top:0.5rem;">
    Photo by <a href="{img_data['profile']}?utm_source=your_app&utm_medium=referral" target="_blank">{img_data['photographer']}</a>
    on <a href="https://unsplash.com/?utm_source=your_app&utm_medium=referral" target="_blank">Unsplash</a>
  </figcaption>
</figure>
""".strip()


def inject_image(content, img_html, position):
    """تحط الصورة فالمكان الصحيح داخل المقال"""
    if not img_html:
        return content

    if position == "بعد العنوان مباشرة":
        # بعد أول فقرة <p>
        match = re.search(r"</p>", content)
        if match:
            idx = match.end()
            return content[:idx] + "\n" + img_html + "\n" + content[idx:]
        return img_html + "\n" + content

    elif position == "في المنتصف":
        # بعد أول <h2>
        match = re.search(r"</h2>", content)
        if match:
            idx = match.end()
            return content[:idx] + "\n" + img_html + "\n" + content[idx:]
        return content + "\n" + img_html

    else:  # في الأخير
        return content + "\n" + img_html


# ============================================================
# 7. دالة توليد المقال
# ============================================================
def generate_article(topic, keywords, language, length, tone, faq, conclusion, meta, part_num, model, temp):
    try:
        prompt = build_prompt(topic, keywords, language, length, tone, faq, conclusion, meta, part_num)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional SEO content writer. Always follow the formatting and language instructions exactly."},
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=temp,
            max_tokens=3000,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"<p><b>خطأ:</b> {str(e)}</p>"

# ============================================================
# 8. استخراج الـ Meta Description
# ============================================================
def extract_meta(content):
    for line in content.split("\n"):
        if line.strip().startswith("META:"):
            return line.replace("META:", "").strip()
    return ""

# ============================================================
# 9. إحصائيات لحظية
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="stat-card">
        <div class="number">{len(st.session_state.generated_articles)}</div>
        <div class="label">مقالات مولّدة</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="stat-card">
        <div class="number">{st.session_state.total_words:,}</div>
        <div class="label">كلمة مكتوبة</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="stat-card">
        <div class="number">{len(keywords)}</div>
        <div class="label">كلمات مفتاحية</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="stat-card">
        <div class="number">{num_to_generate}</div>
        <div class="label">مقالات مجدولة</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# 10. زر الإنتاج + زر المسح
# ============================================================
btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 3])
with btn_col1:
    start_btn = st.button("🔥 ابدأ عملية الإنتاج الضخم!", use_container_width=True)
with btn_col2:
    clear_btn = st.button("🗑️ مسح الكل", use_container_width=True)

if clear_btn:
    st.session_state.generated_articles = []
    st.session_state.total_words = 0
    st.rerun()

# ============================================================
# 11. عملية الإنتاج
# ============================================================
if start_btn:
    if not main_niche.strip():
        st.warning("⚠️ دخل النيش الرئيسي من فضلك!")
        st.stop()

    progress_bar = st.progress(0)
    status_text  = st.empty()

    for i in range(num_to_generate):
        status_text.markdown(f"⚙️ جاري كتابة المقال **{i+1}** من **{num_to_generate}**...")
        progress_bar.progress((i) / num_to_generate)

        content = generate_article(
            main_niche, keywords, language, article_length,
            article_tone, include_faq, include_conclusion, include_meta,
            i + 1, model_choice, temperature
        )

        # --- Unsplash ---
        img_data = None
        img_html = ""
        if include_image and UNSPLASH_KEY:
            search_query = keywords[i % len(keywords)] if keywords else main_niche
            img_data = fetch_unsplash_image(search_query)
            if img_data:
                img_html = build_image_html(img_data, main_niche)
                content  = inject_image(content, img_html, image_position)

        meta_desc  = extract_meta(content) if include_meta else ""
        word_count = len(content.split())
        timestamp  = datetime.now().strftime("%H:%M:%S")

        article_data = {
            "id":         len(st.session_state.generated_articles) + 1,
            "title":      f"{main_niche} — Part {i+1}",
            "content":    content,
            "meta":       meta_desc,
            "words":      word_count,
            "language":   language,
            "timestamp":  timestamp,
            "keywords":   keywords,
            "image":      img_data,
        }
        st.session_state.generated_articles.append(article_data)
        st.session_state.total_words += word_count

        if i < num_to_generate - 1:
            time.sleep(1.5)

    progress_bar.progress(1.0)
    status_text.markdown(f"""<div class="success-banner">
        ✅ تم! كتبنا <b>{num_to_generate}</b> مقال بنجاح. مجموع الكلمات: <b>{st.session_state.total_words:,}</b>
    </div>""", unsafe_allow_html=True)

# ============================================================
# 12. عرض المقالات المولّدة
# ============================================================
if st.session_state.generated_articles:
    st.markdown("---")
    st.markdown("## 📚 المقالات المولّدة")

    # --- زر تحميل ZIP ---
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for art in st.session_state.generated_articles:
            filename = f"article_{art['id']}_{art['language']}.html"
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="description" content="{art['meta']}">
<title>{art['title']}</title>
</head>
<body>
{art['content']}
</body>
</html>"""
            zf.writestr(filename, html_content)

    st.download_button(
        label="📦 تحميل كل المقالات (ZIP)",
        data=zip_buffer.getvalue(),
        file_name=f"articles_{main_niche.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
        mime="application/zip",
        use_container_width=False,
    )

    # --- عرض كل مقال ---
    for art in st.session_state.generated_articles:
        with st.expander(f"📖 مقال #{art['id']} | {art['words']:,} كلمة | {art['language']} | {art['timestamp']}", expanded=False):

            # Keywords tags
            if art["keywords"]:
                kw_html = " ".join(f'<span class="keyword-tag">🔑 {k}</span>' for k in art["keywords"][:6])
                st.markdown(kw_html, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

            # Meta description
            if art["meta"]:
                st.info(f"🔍 **Meta Description:** {art['meta']}")

            # Unsplash image preview
            if art.get("image"):
                img = art["image"]
                img_col1, img_col2 = st.columns([1, 3])
                with img_col1:
                    st.image(img["thumb"], use_container_width=True)
                with img_col2:
                    st.markdown(f"""
📸 **الصورة:** {img['alt'] or main_niche}
👤 **المصور:** [{img['photographer']}]({img['profile']})
🔗 [شوف على Unsplash]({img['unsplash_url']})
                    """)
            elif include_image and not UNSPLASH_KEY:
                st.warning("🖼️ ما تولداتش الصورة — حط UNSPLASH_ACCESS_KEY فـ Secrets.")

            # Tabs: معاينة / HTML
            tab_preview, tab_html, tab_txt = st.tabs(["👁️ معاينة", "🖥️ HTML", "📄 نص خام"])

            with tab_preview:
                st.markdown(art["content"], unsafe_allow_html=True)

            with tab_html:
                st.code(art["content"], language="html")

            with tab_txt:
                plain = re.sub(r"<[^>]+>", "", art["content"]).strip()
                st.text_area("نص خام:", plain, height=300, key=f"txt_{art['id']}")

            # أزرار تحميل فردية
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    "⬇️ HTML",
                    data=art["content"],
                    file_name=f"article_{art['id']}.html",
                    mime="text/html",
                    key=f"html_{art['id']}",
                )
            with dl_col2:
                plain_dl = re.sub(r"<[^>]+>", "", art["content"]).strip()
                st.download_button(
                    "⬇️ TXT",
                    data=plain_dl,
                    file_name=f"article_{art['id']}.txt",
                    mime="text/plain",
                    key=f"txt_dl_{art['id']}",
                )

# ============================================================
# 13. Footer
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#4a5568; font-size:0.85rem; padding:1rem;">
    🏭 <b>AI Content Factory v2.0</b> — Developed by Mouhcine Digital Systems<br>
    Powered by <b>Groq</b> & <b>Llama 3.1</b> | Built with ❤️ using Streamlit
</div>
""", unsafe_allow_html=True)
