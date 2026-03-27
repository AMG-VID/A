import requests
import re

def get_movies():
    all_content = []
    # نستخدم مصدر بيانات مفتوح (TMDB API أو RSS Feed عام)
    # هنا جلبنا قائمة أفلام حديثة من مصدر وسيط لا يحجب GitHub
    api_url = "https://api.themoviedb.org"
    
    try:
        print("📡 جلب البيانات من القاعدة السحابية...")
        response = requests.get(api_url, timeout=20)
        data = response.json()
        
        for movie in data['results'][:12]:
            all_content.append({
                "title": movie['title'],
                "img": f"https://image.tmdb.org{movie['poster_path']}",
                "link": f"https://www.google.com+{movie['title']}+mycima", # رابط بحث ذكي
                "source": "قاعدة البيانات"
            })
        print(f"✅ تم جلب {len(all_content)} فيلم بنجاح!")
    except Exception as e:
        print(f"❌ فشل الجلب: {e}")
            
    return all_content

def update_html(data):
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    cards = ""
    for m in data:
        cards += f'''
        <div class="movie-card">
            <img src="{m['img']}" alt="{m['title']}">
            <div class="movie-info">
                <span class="badge">تحديث آلي</span>
                <h5 style="color:white; font-size:0.9rem; margin:10px 0;">{m['title']}</h5>
                <a href="{m['link']}" class="play-link" target="_blank" style="background:red; color:white; padding:5px 15px; text-decoration:none; border-radius:5px; display:block;">بحث عن المشاهدة</a>
            </div>
        </div>'''

    new_html = re.sub(r"<!-- MOVIES_START -->.*?<!-- MOVIES_END -->", f"<!-- MOVIES_START -->\n{cards}\n<!-- MOVIES_END -->", html, flags=re.DOTALL)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)

if __name__ == "__main__":
    movies = get_movies()
    if movies:
        update_html(movies)
