import requests
import re

# روابط البحث المباشرة (هذه الروابط نادراً ما تُحجب)
SOURCES = {
    "ماي سيما": "https://mycima.pw",
    "ايجي بست": "https://egybest.media",
    "لاروزا": "https://laroza.site"
}

def get_movies():
    all_content = []
    # نستخدم User-Agent قوي جداً لمحاكاة متصفح حقيقي 100%
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    
    for name, url in SOURCES.items():
        try:
            print(f"📡 محاولة اختراق حماية {name}...")
            # نستخدم بروكسي مجاني بسيط لتغيير عنوان الـ IP الخاص بـ GitHub
            proxied_url = f"https://api.allorigins.win{url}"
            response = requests.get(proxied_url, timeout=20)
            data = response.json()
            html = data['contents']
            
            # البحث عن الصور والروابط باستخدام Regex (أسرع وأدق في حالة الحماية)
            # نبحث عن نمط: رابط يحتوي على صورة
            matches = re.findall(r'<a href="(.*?)".*?src="(.*?)" alt="(.*?)"', html)
            
            count = 0
            for link, img, title in matches:
                if count < 8 and len(title) > 5:
                    all_content.append({
                        "title": title.strip(),
                        "img": img if img.startswith('http') else "https:" + img,
                        "link": link if link.startswith('http') else "https://" + link.split('/')[2] + link,
                        "source": name
                    })
                    count += 1
            print(f"✅ تم جلب {count} فيلم من {name}")
        except Exception as e:
            print(f"❌ فشل في {name}: {e}")
            
    return all_content

def update_html(data):
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    cards = ""
    for m in data:
        cards += f'''
        <div class="movie-card">
            <img src="{m['img']}" alt="{m['title']}" onerror="this.src='https://via.placeholder.com'">
            <div class="movie-info">
                <span class="badge">{m['source']}</span>
                <h5>{m['title']}</h5>
                <a href="{m['link']}" class="play-link" target="_blank">مشاهدة</a>
            </div>
        </div>'''

    new_html = re.sub(r"<!-- MOVIES_START -->.*?<!-- MOVIES_END -->", f"<!-- MOVIES_START -->\n{cards}\n<!-- MOVIES_END -->", html, flags=re.DOTALL)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    movies = get_movies()
    if movies:
        update_html(movies)
        print("🎉 الموقع الآن يحتوي على أفلام!")
    else:
        print("🤷‍♂️ لا تزال المواقع ترفض الروبوت، سأحاول بطريقة بديلة في التحديث القادم.")
