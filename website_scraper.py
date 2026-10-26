import json
import os
import re
from typing import List, Dict, Any, Optional

class WebsiteScraper:
    """
    WayMate Knowledge Base & Search Engine
    Manages structured information for WayMate (trips, maintenance, navigation, settings, profiles).
    Supports multi-keyword scored search, tag ranking, and dynamic synchronization with waymate-client.
    """
    def __init__(self, base_url: str = "http://localhost:8782", data_file: str = "scraped_website.json"):
        self.base_url = base_url.rstrip('/')
        self.data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file)
        self.scraped_data: List[Dict[str, Any]] = []
        self.load_data()

    def load_data(self):
        """Load knowledge base from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.scraped_data = json.load(f)
            except Exception as e:
                print(f"[KnowledgeBase] Error loading data file: {e}")
                self.scraped_data = []
        else:
            self.refresh_from_client()

    def refresh_from_client(self):
        """Re-generate knowledge from build_waymate_knowledge module"""
        try:
            from build_waymate_knowledge import generate_waymate_knowledge
            self.scraped_data = generate_waymate_knowledge()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
            print(f"[KnowledgeBase] Refreshed {len(self.scraped_data)} entries from WayMate client")
        except Exception as e:
            print(f"[KnowledgeBase] Failed to refresh from client: {e}")

    def scrape_urls(self):
        """Synchronize with client data"""
        self.refresh_from_client()

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Scored search engine matching queries against titles, tags, and content.
        Ranks entries by relevance score instead of brittle literal substring matching.
        """
        if not self.scraped_data:
            self.load_data()
            if not self.scraped_data:
                return []

        clean_query = query.lower().strip()
        if not clean_query:
            return self.scraped_data[:max_results]

        # Stop words to ignore during scoring
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'with',
            'of', 'by', 'about', 'can', 'you', 'me', 'my', 'how', 'what', 'which', 'where', 'when',
            'why', 'do', 'does', 'did', 'i', 'tell', 'show', 'give', 'là', 'của', 'và', 'có', 'trong',
            'cho', 'với', 'ở', 'được', 'như', 'thế', 'nào', 'gì', 'sao', 'làm'
        }

        # Tokenize query
        tokens = [word for word in re.findall(r'[\w\d]+', clean_query) if len(word) > 1 and word not in stop_words]
        if not tokens:
            tokens = [clean_query]

        scored_results = []
        for entry in self.scraped_data:
            score = 0
            title = entry.get('title', '').lower()
            content = entry.get('content', '').lower()
            metadata = entry.get('metadata', {})
            tags = [t.lower() for t in metadata.get('tags', [])]
            category = metadata.get('category', '').lower()
            doc_type = metadata.get('type', '').lower()

            # Exact phrase match gives huge boost
            if clean_query in title:
                score += 50
            if clean_query in content:
                score += 30

            # Match individual tokens
            for token in tokens:
                # Title matches
                if token in title:
                    score += 15
                # Tags matches
                if any(token in tag for tag in tags):
                    score += 20
                # Category or type matches
                if token in category or token in doc_type:
                    score += 10
                # Content frequency
                occurrences = content.count(token)
                if occurrences > 0:
                    score += min(occurrences * 3, 24)

            # Special keyword associations
            if any(k in clean_query for k in ['oil', 'nhớt', 'thay nhớt', 'maintenance', 'bảo dưỡng', 'odo', 'km']):
                if 'maintenance' in title or 'garage' in tags or 'oil' in content:
                    score += 25

            if any(k in clean_query for k in ['hà giang', 'ha giang', 'mã pí lèng', 'ma pi leng', 'mèo vạc', 'đồng văn']):
                if 'ha giang' in title or 'ha giang' in tags:
                    score += 35

            if any(k in clean_query for k in ['đà lạt', 'da lat', 'sài gòn', 'saigon', 'prenn', 'tuyền lâm']):
                if 'da lat' in title or 'da lat' in tags:
                    score += 35

            if any(k in clean_query for k in ['google maps', 'bản đồ', 'map', 'navigation', 'gpx', 'gps']):
                if 'navigation' in title or 'google maps' in title or 'gpx' in content:
                    score += 25

            if any(k in clean_query for k in ['password', 'mật khẩu', 'quên mật khẩu', 'otp', 'login', 'đăng nhập']):
                if 'auth' in tags or 'password' in title:
                    score += 25

            if any(k in clean_query for k in ['mũ bảo hiểm', 'helmet', 'bảo hộ', 'gear', 'safety']):
                if 'safety' in tags or 'gear' in title:
                    score += 25

            if score > 0:
                scored_results.append((score, entry))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        results = [entry for _, entry in scored_results[:max_results]]
        
        # If no scored match found, fall back to returning default high-priority guides
        if not results:
            results = self.scraped_data[:max_results]

        return results