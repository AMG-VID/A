import requests
from bs4 import BeautifulSoup
import re

# روابط المواقع المحدثة مع رأس طلب (Headers) لمحاكاة متصفح حقيقي
SOURCES = {
    "mycima": "https://mycima.pw",
    "egibest": "https://egibest.monster",
    "laroza": "https://laroza.vip"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3'
}

def get_movies():
    all_content = []
    for name, url in SOURCES.items():
        try:
            print(f"جاري محاولة سحب الأفلام من {name}...")
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            # محاولة البحث عن العناصر بأكثر من طريقة لأن الكلاسات تتغير
            items = soup.select('.GridItem') or soup.select('.movie-item') or soup.find_all('div', class_=re.compile('box|item|card'))
            
            for item in items[:6]:
                title = item.find(['h2', 'h3', 'h4'])
                img = item.find('img')
                link = item.find('a')
                
                if title and img and link:
                    all_content.append({
                        "title": title.text.strip(),
                        "img": img.get('src') or img.get('data-src'),
                        "link": link.get('href'),
                        "source": name
                    })
        except Exception as e:
            print(f"فشل السحب من {name}: {e}")
            
    return all_content

def update_html(data):
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    cards_html = ""
    for m in data:
        cards_html += f'''
        <div class="movie-card">
            <img src="{m['img']}" alt="{m['title']}">
            <div class="movie-info">
                <span class="badge">{m['source']}</span>
                <h5>{m['title']}</h5>
                <a href="{m['link']}" class="play-link" target="_blank">مشاهدة الآن</a>
            </div>
        </div>'''

    pattern = r"<!-- MOVIES_START -->.*?<!-- MOVIES_END -->"
    replacement = f"<!-- MOVIES_START -->\n{cards_html}\n<!-- MOVIES_END -->"
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    data = get_movies()
    if data:
        update_html(data)
        print(f"تم بنجاح! تم إضافة {len(data)} فيلم.")
    else:
        print("لم يتم العثور على أي أفلام، جرب تحديث الروابط.")
