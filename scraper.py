import requests
from bs4 import BeautifulSoup
import json

# القائمة المستهدفة (الينابيع)
SOURCES = {
    "mycima": "https://mycima.horse",
    "egibest": "https://egibest.my",
    "laroza": "https://larozaa.com"
}

def get_movies():
    all_content = []
    
    for name, url in SOURCES.items():
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ملاحظة: الكلاسات (Classes) تتغير، هذا مثال هيكلي ستحتاج لضبطه حسب فحصك للموقع
            items = soup.select('.GridItem') or soup.select('.movie-item') 
            
            for item in items[:10]: # جلب أحدث 10 من كل موقع
                title = item.find('h2').text if item.find('h2') else "بدون عنوان"
                img = item.find('img')['src'] if item.find('img') else ""
                link = item.find('a')['href'] if item.find('a') else ""
                
                all_content.append({
                    "title": title,
                    "img": img,
                    "link": link,
                    "source": name
                })
        except:
            print(f"Error connecting to {name}")
            
    return all_content

def update_html(data):
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # تحويل البيانات لكود HTML شيك
    cards_html = ""
    for movie in data:
        cards_html += f'''
        <div class="movie-card" data-source="{movie['source']}">
            <img src="{movie['img']}" alt="{movie['title']}">
            <div class="info">
                <h4>{movie['title']}</h4>
                <a href="{movie['link']}" class="play-btn">شاهد الآن</a>
            </div>
        </div>
        '''

    # حقن الكود بين العلامات التي وضعناها
    start_tag = "<!-- MOVIES_START -->"
    end_tag = "<!-- MOVIES_END -->"
    new_html = html.split(start_tag)[0] + start_tag + cards_html + end_tag + html.split(end_tag)[1]

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    movies = get_movies()
    if movies:
        update_html(movies)
        print("Done! الموقع تحدث بنجاح.")
