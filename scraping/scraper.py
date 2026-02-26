import time
from selenium import webdriver
from bs4 import BeautifulSoup

def scrape_jobs(search_query="Data Scientist"):
    # Antigravity can help you refine these selectors if they change!
    url = f"https://www.linkedin.com/jobs/search/?keywords={search_query}"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # Run without a window
    
    driver = webdriver.Remote(
        command_executor='http://chrome:4444/wd/hub', # Pointing to a Docker Selenium Hub
        options=options
    )
    
    driver.get(url)
    time.sleep(5) # Let JS load
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_cards = soup.find_all('div', class_='base-card')
    
    jobs_data = []
    for card in job_cards:
        title = card.find('h3', class_='base-search-card__title').text.strip()
        company = card.find('h4', class_='base-search-card__subtitle').text.strip()
        # We will grab the link to the full description next
        link = card.find('a', class_='base-card__full-link')['href']
        jobs_data.append({"title": title, "company": company, "link": link})
        
    driver.quit()
    return jobs_data