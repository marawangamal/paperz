import time
from typing import List, Dict, Optional
import requests
from tqdm import tqdm

from base import ConferenceScraper  # Use absolute import


class ICLRScraper(ConferenceScraper):
    """ICLR conference paper scraper"""

    @property
    def conference_name(self) -> str:
        return "ICLR"

    @property
    def full_conference_name(self) -> str:
        return "International Conference on Learning Representations"

    def base_url(self, year: int = None) -> str:
        api_prefix = "api" if year is not None and year <= 2023 else "api2"
        return f"https://{api_prefix}.openreview.net"

    def get_papers(self, year: int) -> List[Dict]:
        """Fetch paper data from JSON endpoint"""
        paper_data = []
        total_count = 0
        try:
            url = f"{self.base_url(year)}/notes?content.venueid=ICLR.cc/{year}/Conference"
            while True:
                response = requests.get(url)
                response.raise_for_status()
                response = response.json()
                notes, count = response["notes"], response["count"]
                paper_data += notes
                total_count += len(notes)
                if total_count < count:
                    url = f"{self.base_url(year)}/notes?content.venueid=ICLR.cc/{year}/Conference&offset={total_count}"
                    time.sleep(self.delay)
                else:
                    break
            return paper_data
        except Exception as e:
            print(f"Error fetching papers for year {year}: {str(e)}")
            return []

    def get_paper_data(self, paper_data: Dict) -> Dict[str, Optional[str]]:
        """Extract paper data"""
        processed_data = {
            "title": None,
            "authors": [],
            "abstract": None,
            "venue_abbrev": self.conference_name,
            "venue_year": paper_data.get("venue_year"),
            "pdf_url": None,
            "code_url": None,
        }

        content = paper_data.get("content")
        if content is None:
            raise ValueError("content is None")

        if (title := content.get("title")):
            processed_data["title"] = title if isinstance(title, str) else title.get("value")
        else:
            raise ValueError("title is None")

        if (authors := content.get("authors")):
            processed_data["authors"] = authors if isinstance(authors, list) else authors.get("value")
        else:
            raise ValueError("authors is None")

        if (id := paper_data.get("id")):
            processed_data["pdf_url"] = f"https://openreview.net?pdf?id={id}"

        if (abstract := content.get("abstract")):
            if isinstance(abstract, dict):
                abstract = abstract.get("value")
            processed_data["abstract"] = abstract
            processed_data["code_url"] = self.extract_github_url(abstract)

        return processed_data

    def scrape_year(self, year: int):
        """Scrape all papers for a given year"""
        print(f"Scraping {self.conference_name} {year}...")

        # Save venue information
        self.save_venue({
            "title": self.full_conference_name,
            "abbrev": self.conference_name,
            "year": year,
        })

        # Get paper data from JSON
        papers = self.get_papers(year)
        if not papers:
            print(f"No papers found for year {year}")
            return

        with tqdm(total=len(papers), desc=f"Year {year}", unit="paper") as pbar:
            for paper in papers:
                try:
                    paper["venue_year"] = year
                    self.save_paper(self.get_paper_data(paper))
                    pbar.update(1)
                except Exception as e:
                    print(f"\nError processing paper: {str(e)}")
                    continue

# Usage example
if __name__ == "__main__":
    # Scrape ICLR papers
    iclr_scraper = ICLRScraper(output_dir='dumps/iclr')
    iclr_scraper.scrape_multiple_years(list(range(2025, 2020, -1)))
