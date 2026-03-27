import requests
from bs4 import BeautifulSoup
import re

# الينابيع الرقمية المحدثة (أحدث روابط تعمل الآن)
SOURCES = {
    "ماي سيما": "https://mycima.pw",
    "ايجي بست": "https://egybest.media",
    "لاروزا": "https://laroza.site"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def get_movies():
    all_content = []
    print("🚀 بدء عملية الصيد الرقمي...")
    
    for name, url in SOURCES.items():
        try:
            print(f"🔎 فحص {name}...")
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                print(f"❌ {name} لم يستجب.")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # استراتيجية البحث عن "البصمة": أي رابط يحتوي على صورة داخله
            # المواقع تغير الكلاسات لكنها لا تغير هيكل (رابط > صورة)
            items = soup.find_all('a', href=True)
            
            count = 0
            for a in items:
                img = a.find('img')
                if img and count < 10:  # نجلب أحدث 10 من كل موقع
                    title = img.get('alt') or a.get('title') or "فيلم جديد"
                    img_src = img.get('data-src') or img.get('src') or img.get('data-lazy-src')
                    link = a['href']
                    
                    # تصحيح الروابط الناقصة
                    if link.startswith('/'): link = url.rstrip('/') + link
                    if img_src and img_src.startswith('/'): img_src = url.rstrip('/') + img_src
                    
                    # تصفية النتائج (نتأكد أنه فيلم وليس أيقونة صغيرة)
                    if img_src and len(title) > 5 and "http" in img_src:
                        all_content.append({
                            "title": title.strip(),
                            "img": img_src,
                            "link": link,
                            "source": name
                        })
                        count += 1
            print(f"✅ تم سحب {count} مواد من {name}")
        except Exception as e:
            print(f"⚠️ خطأ في {name}: {e}")
            
    return all_content

def update_html(data):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        # بناء كود الـ HTML بتنسيق شيك متوافق مع تصميمك
        movies_html = ""
        for m in data:
            movies_html += f'''
            <div class="movie-card">
                <img src="{m['img']}" alt="{m['title']}" loading="lazy" onerror="this.src='https://via.placeholder.com'">
                <div class="movie-info">
                    <span class="badge">{m['source']}</span>
                    <h5 style="color:white; font-size:0.9rem; margin:10px 0; height:40px; overflow:hidden;">{m['title']}</h5>
                    <a href="{m['link']}" class="play-link" target="_blank" style="background:red; color:white; padding:8px 15px; text-decoration:none; border-radius:5px; display:block; font-weight:bold;">مشاهدة الآن</a>
                </div>
            </div>'''

        # عملية الحقن النووي بين العلامات
        pattern = r"<!-- MOVIES_START -->.*?<!-- MOVIES_END -->"
        replacement = f"<!-- MOVIES_START -->\n{movies_html}\n<!-- MOVIES_END -->"
        
        # التأكد من وجود العلامات في الملف
        if "<!-- MOVIES_START -->" not in html_content:
            print("❌ خطأ: لم أجد علامة <!-- MOVIES_START --> في ملف index.html")
            return

        new_html = re.sub(pattern, replacement, html_content, flags=re.DOTALL)

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("🎉 تم تحديث ملف index.html بنجاح!")
        
    except Exception as e:
        print(f"❌ فشل تحديث الـ HTML: {e}")

if __name__ == "__main__":
    movies = get_movies()
    if movies:
        update_html(movies)
    else:
        print("📭 لم يتم العثور على أي محتوى، تحقق من الروابط.")
