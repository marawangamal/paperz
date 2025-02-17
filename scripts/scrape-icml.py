"""This script only works on the latest ICML website (2020-present)

Use the endpoint `/static/virtual/data/icml-{year}-orals-posters.json` to fetch paper data
"""
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from tqdm import tqdm

from base import ConferenceScraper  # Use absolute import


class ICMLScraper(ConferenceScraper):
    """ICML conference paper scraper"""
    
    @property
    def base_url(self) -> str:
        return "https://icml.cc"
    
    @property
    def conference_name(self) -> str:
        return "ICML"
    
    @property
    def full_conference_name(self) -> str:
        return "International Conference on Machine Learning"
    
    def get_paper_data(self, year: int) -> List[Dict]:
        """Fetch paper data from JSON endpoint"""
        try:
            response = self.make_request(f"/static/virtual/data/icml-{year}-orals-posters.json")
            return response.json()['results']
        except Exception as e:
            print(f"Error fetching papers for year {year}: {str(e)}")
            return []
    
    def get_paper_urls(self, paper_data: Dict) -> Dict[str, Optional[str]]:
        """Extract PDF and code URLs from paper data"""
        urls = {
            'pdf_url': None,
            'code_url': None
        }
        
        if paper_data.get('paper_pdf_url'):
            urls['pdf_url'] = paper_data['paper_pdf_url']
        if paper_data.get('abstract'):
            urls['code_url'] = self.extract_github_url(paper_data['abstract'])
        
        return urls
    
    def scrape_year(self, year: int):
        """Scrape all papers for a given year"""
        print(f"Scraping {self.conference_name} {year}...")
        
        # Save venue information
        self.save_venue_info(year)
        
        # Get paper data from JSON
        papers = self.get_paper_data(year)
        if not papers:
            print(f"No papers found for year {year}")
            return
        
        with tqdm(total=len(papers), desc=f"Year {year}", unit="paper") as pbar:
            for paper in papers:
                try:
                    urls = self.get_paper_urls(paper)
                    paper_data = {
                        'title': paper.get('name', ''),
                        'authors': [author['fullname'] for author in paper.get('authors', [])],
                        'abstract': paper.get('abstract', ''),
                        'pdf_url': paper.get('paper_pdf_url'),
                        'code_url': urls['code_url']
                    }
                    
                    self.save_paper_info(paper_data, year)
                    pbar.update(1)
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"\nError processing paper: {str(e)}")
                    continue

# Usage example
if __name__ == "__main__":
    # Scrape ICML papers
    icml_scraper = ICMLScraper(output_dir='dumps/icml')
    icml_scraper.scrape_multiple_years(list(range(2024, 2020, -1)))