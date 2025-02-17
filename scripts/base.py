from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from tqdm import tqdm

class ConferenceScraper(ABC):
    """Base class for conference paper scrapers"""
    
    def __init__(self, output_dir: str = 'data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.delay = 0.2  # Default delay between requests
        
        # Setup CSV files
        self.setup_csv_files()
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the conference website"""
        pass
    
    @property
    @abstractmethod
    def conference_name(self) -> str:
        """Name of the conference"""
        pass
    
    @property
    def full_conference_name(self) -> str:
        """Full name of the conference - can be overridden"""
        return self.conference_name
    
    def setup_csv_files(self):
        """Setup CSV files with appropriate headers"""
        # Setup venues CSV
        venues_path = self.output_dir / 'venues.csv'
        if not venues_path.exists():
            with open(venues_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'abbrev', 'year'])

        # Setup papers CSV
        papers_path = self.output_dir / 'papers.csv'
        if not papers_path.exists():
            with open(papers_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'title', 'authors', 'abstract', 'venue_abbrev', 
                    'venue_year', 'pdf_url', 'code_url'
                ])
    
    def save_venue_info(self, year: int):
        """Save venue information for the given year"""
        with open(self.output_dir / 'venues.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.full_conference_name,
                self.conference_name,
                year,
            ])
    
    def save_paper_info(self, paper_data: Dict, year: int):
        """Save paper information to CSV"""
        with open(self.output_dir / 'papers.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                paper_data.get('title', ''),
                '|'.join(paper_data.get('authors', [])),
                paper_data.get('abstract', ''),
                self.conference_name,
                year,
                paper_data.get('pdf_url'),
                paper_data.get('code_url')
            ])

    def scrape_multiple_years(self, years: List[int]):
        """Scrape papers from multiple years"""
        for year in years:
            try:
                self.scrape_year(year)
            except Exception as e:
                print(f"Error processing year {year}: {str(e)}")
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make HTTP request with error handling and rate limiting"""
        full_url = urljoin(self.base_url, url)
        response = self.session.request(method, full_url, **kwargs)
        response.raise_for_status()
        time.sleep(self.delay)
        return response
    
    def extract_github_url(self, text: str) -> Optional[str]:
        """Extract GitHub URL from text"""
        import re
        github_urls = re.findall(r'https?://github\.com/[^\s)+\]]+', text.lower())
        return github_urls[0] if github_urls else None
    
    def get_metadata_from_citation_tags(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from citation meta tags"""
        metadata = {}
        
        title_tag = soup.find('meta', {'name': 'citation_title'})
        metadata['title'] = title_tag['content'] if title_tag else ''
        
        author_tags = soup.find_all('meta', {'name': 'citation_author'})
        metadata['authors'] = [tag['content'] for tag in author_tags]
        
        pdf_tag = soup.find('meta', {'name': 'citation_pdf_url'})
        metadata['pdf_url'] = pdf_tag['content'] if pdf_tag else None
        
        # Get abstract - find the h4 header and get the next p tag
        abstract_header = soup.find('h4', text=re.compile('Abstract', re.IGNORECASE))
        if abstract_header and abstract_header.find_next('p'):
            metadata['abstract'] = abstract_header.find_next('p').text.strip()
        else:
            metadata['abstract'] = ''
        
        return metadata
    
    @abstractmethod
    def scrape_year(self, year: int):
        """Scrape all papers for a given year"""
        pass