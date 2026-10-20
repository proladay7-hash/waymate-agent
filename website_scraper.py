import json
import os
import time
from typing import List, Dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

class WebsiteScraper:
    def __init__(self, base_url: str, data_file: str = 'scraped_website.json', wait_selector: str = '#root'):
        self.base_url = base_url.rstrip('/')
        self.data_file = data_file
        self.wait_selector = wait_selector  # CSS selector to wait for
        self.scraped_data = []
        self.previous_content = {}
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.scraped_data = json.load(f)
                self.previous_content = {entry['url']: entry['content'] for entry in self.scraped_data}

    def get_all_urls(self) -> List[str]:
        # Static routes from frontend
        static_routes = [
            '/', '/login', '/register', '/forgot', '/reset', '/about', '/magazine', '/contact', '/help',
            '/privacy', '/terms', '/cookies', '/categories', '/cart', '/wishlist', '/profile', '/orders', '/payment', '/admin'
        ]
        urls = [self.base_url + route for route in static_routes]
        # Dynamic product routes
        try:
            backend_api = 'http://localhost:8080/api/bikes/all'
            resp = requests.get(backend_api, timeout=10)
            resp.raise_for_status()
            bikes = resp.json()
            for bike in bikes:
                urls.append(f"{self.base_url}/product/{bike['id']}")
        except Exception as e:
            print(f"Failed to fetch bikes for product URLs: {e}")
        return urls

    def is_loading_content(self, text: str) -> bool:
        loading_phrases = [
            'Loading Big Bike Blitz',
            'Your premium motorcycle experience is loading',
            'Loading...'
        ]
        for phrase in loading_phrases:
            if phrase.lower() in text.lower():
                return True
        return False

    def scrape_urls(self):
        urls = self.get_all_urls()
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Run in non-headless mode for debugging
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.scraped_data = []

        # Inject JWT token into localStorage
        # jwt_token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJBRE1JTiIsImlhdCI6MTc1MTg5NDg5MCwiZXhwIjoxNzUxOTMwODkwfQ.WW9iCDyfqddNPXYy24zXg_junzgb5eATtWla9-yMmro'
        # driver.get(self.base_url)
        # driver.execute_script("window.localStorage.setItem('jwt', arguments[0]);", jwt_token)
        # driver.refresh()

        for url in urls:
            print(f"Scraping: {url}")
            try:
                driver.get(url)
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, self.wait_selector))
                    )
                    time.sleep(3)  # Wait extra for React to render
                except Exception as e:
                    print(f"Timeout waiting for content on {url}: {e}")
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                title = soup.title.string.strip() if soup.title and soup.title.string else url
                for tag in soup(['script', 'style']):
                    tag.decompose()
                text = soup.get_text(separator=' ', strip=True)
                # Skip if content is a loading message or same as previous crawl
                if self.is_loading_content(text):
                    print(f"Skipped loading page for {url}")
                    continue
                if url in self.previous_content and self.previous_content[url] == text:
                    print(f"Skipped unchanged content for {url}")
                    continue
                self.scraped_data.append({'url': url, 'title': title, 'content': text})
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
        driver.quit()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        print(f"Scraped {len(self.scraped_data)} pages.")

    def search(self, keyword: str, max_results: int = 5) -> List[Dict]:
        if not self.scraped_data:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.scraped_data = json.load(f)
            else:
                print("No scraped data found. Please run scrape_urls() first.")
                return []
        results = []
        for entry in self.scraped_data:
            if keyword.lower() in entry['content'].lower():
                results.append(entry)
                if len(results) >= max_results:
                    break
        return results

# Example usage:
# scraper = WebsiteScraper(base_url='http://localhost:5173', wait_selector='#root')
# scraper.scrape_urls()
# print(scraper.search('motorcycle')) 