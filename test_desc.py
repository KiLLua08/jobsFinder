import os
import django
import urllib.request
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from scraping.models import JobListing

job = JobListing.objects.filter(description='').first()
if job:
    print('Testing URL:', job.link)
    req = urllib.request.Request(
        job.link, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            print('Page Title:', soup.title.string if soup.title else 'No Title')
            
            # Print all div classes that contain 'description'
            containers = soup.find_all('div', class_=lambda x: x and 'description' in x.lower())
            print("Possible description divs found:", len(containers))
            for c in containers: 
                print("- ", c.get('class'))
                
            # Print text of first description container to see if it holds the job desc
            if containers:
                print("First container preview:")
                print(containers[0].get_text(separator=' ', strip=True)[:200])
    except Exception as e:
        print(f"Failed to fetch {job.link}: {e}")
else:
    print('No jobs with empty descriptions.')
