import requests
from bs4 import BeautifulSoup
import re

# الروابط المباشرة للأقسام لضمان الوصول للمحتوى
SOURCES = {
    "ماي سيما": "https://mycima.pw",
    "ايجي بست": "https://egibest.monster",
    "لاروزا": "https://laroza.vip"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_movies():
    all_content = []
    for name, url in SOURCES.items():
        try:
            print(f"جاري البحث في {name}...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ابحث عن أي div يحتوي على رابط وصورة (نمط الفيلم المشترك)
            items = soup.find_all(['div', 'article'], limit=15)
            
            count = 0
            for item in items:
                link_el = item.find('a', href=True)
                img_el = item.find('img')
                
                if link_el and img_el and count < 8:
                    title = img_el.get('alt') or link_el.get('title') or "فيلم جديد"
                    img_url = img_el.get('data-src') or img_el.get('src') or ""
                    # تأكد أن الرابط كامل
                    link_url = link_el['href']
                    if link_url.startswith('/'): link_url = url.split('.com')[0] + '.com' + link_url
                    
                    if img_url and len(title) > 5:
                        all_content.append({
                            "title": title.strip(),
                            "img": img_url,
                            "link": link_url,
                            "source": name
                        })
                        count += 1
        except: continue
    return all_content

def update_html(data):
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    cards_html = ""
    for m in data:
        cards_html += f'''
        <div class="movie-card">
            <img src="{m['img']}" alt="{m['title']}" onerror="this.src='https://via.placeholder.com'">
            <div class="movie-info">
                <span class="badge">{m['source']}</span>
                <h5 style="color:white; font-size:0.9rem; margin:10px 0;">{m['title']}</h5>
                <a href="{m['link']}" class="play-link" target="_blank" style="background:red; color:white; padding:5px 15px; text-decoration:none; border-radius:5px;">شاهد الآن</a>
            </div>
        </div>'''

    # الحقن الذكي
    pattern = r"<!-- MOVIES_START -->.*?<!-- MOVIES_END -->"
    replacement = f"<!-- MOVIES_START -->\n{cards_html}\n<!-- MOVIES_END -->"
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    movies = get_movies()
    if movies:
        update_html(movies)
        print(f"تم بنجاح! أضفنا {len(movies)} فيلم للموقع.")
    else:
        print("لم يتم العثور على محتوى، تأكد من روابط المواقع.")
