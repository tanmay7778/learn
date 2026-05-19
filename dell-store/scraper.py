from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time


class DellScraper:
    """Scrapes product details from Dell India website."""

    def __init__(self):
        self.base_url = "https://www.dell.com/en-in"
        self.driver = None

    def _init_driver(self):
        """Initialize headless Chrome browser."""
        options = Options()
        options.add_argument("--headless")  # Run without opening browser
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def _close_driver(self):
        if self.driver:
            self.driver.quit()

    def scrape_category(self, category_url):
        """
        Scrape all products from a category page.
        Returns list of product dicts.
        """
        self._init_driver()
        products = []

        try:
            full_url = f"{self.base_url}{category_url}"
            self.driver.get(full_url)
            time.sleep(3)  # Wait for JS to load

            # Scroll to load all products (infinite scroll handling)
            self._scroll_page()

            # Parse product cards
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            product_cards = soup.find_all("div", class_="ps-stack")

            for card in product_cards:
                product = self._parse_product_card(card)
                if product:
                    products.append(product)

        except Exception as e:
            print(f"Error scraping {category_url}: {e}")
        finally:
            self._close_driver()

        return products

    def scrape_product_detail(self, product_url):
        """
        Scrape detailed specs from a single product page.
        """
        self._init_driver()
        details = {}

        try:
            self.driver.get(product_url)
            time.sleep(3)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Product name
            title = soup.find("h1", class_="ps-title")
            details["name"] = title.text.strip() if title else "Unknown"

            # Price (Dell MRP)
            price_elem = soup.find("div", class_="ps-dell-price")
            if price_elem:
                price_text = price_elem.text.strip().replace(",", "").replace("\u20b9", "")
                details["dell_mrp"] = float(price_text) if price_text.replace(".", "").isdigit() else 0

            # Specs table
            specs_section = soup.find("div", id="spec-section")
            if specs_section:
                specs = {}
                rows = specs_section.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        key = cols[0].text.strip().lower()
                        value = cols[1].text.strip()
                        specs[key] = value

                details["processor"] = specs.get("processor", "")
                details["ram"] = specs.get("memory", specs.get("ram", ""))
                details["storage"] = specs.get("hard drive", specs.get("storage", ""))
                details["display"] = specs.get("display", specs.get("screen", ""))
                details["graphics"] = specs.get("graphics card", specs.get("video card", ""))
                details["os"] = specs.get("operating system", "")
                details["weight"] = specs.get("weight", "")

            # Product image
            img = soup.find("img", class_="ps-image")
            details["image_url"] = img["src"] if img and img.get("src") else ""
            details["dell_url"] = product_url

        except Exception as e:
            print(f"Error scraping product: {e}")
        finally:
            self._close_driver()

        return details

    def _scroll_page(self, scrolls=5):
        """Scroll down to trigger lazy-loaded products."""
        for _ in range(scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

    def _parse_product_card(self, card):
        """Extract basic info from a product card element."""
        try:
            name_elem = card.find("h3", class_="ps-title")
            link_elem = card.find("a", href=True)
            price_elem = card.find("div", class_="ps-dell-price")
            img_elem = card.find("img")

            return {
                "name": name_elem.text.strip() if name_elem else None,
                "dell_url": self.base_url + link_elem["href"] if link_elem else None,
                "dell_mrp": self._clean_price(price_elem.text) if price_elem else 0,
                "image_url": img_elem["src"] if img_elem and img_elem.get("src") else "",
            }
        except Exception:
            return None

    def _clean_price(self, price_text):
        """Convert Rs.74,990.00 -> 74990.0"""
        cleaned = price_text.strip().replace(",", "").replace("\u20b9", "").replace(" ", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


if __name__ == "__main__":
    # Test the scraper
    scraper = DellScraper()
    laptops = scraper.scrape_category("/shop/laptops/new")
    print(f"Found {len(laptops)} laptops")
    for laptop in laptops[:3]:
        print(f"  - {laptop['name']} | Rs.{laptop['dell_mrp']}")
