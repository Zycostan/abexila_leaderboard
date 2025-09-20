import os
import json
import requests
import csv
import time
import gzip
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Tuple, Optional, Set

class StoneworksDataScraper:
    def __init__(self):
        self.base_map_url = "https://map.stoneworks.gg/abex1"
        self.wiki_base_url = "https://stoneworksmc.fandom.com"
        self.markers_url = "https://map.stoneworks.gg/abex1/maps/abexilas/live/markers.json?331762"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Data storage
        self.nations_data: List[Dict] = []
        self.cities_data: List[Dict] = []
        self.territories_data: List[Dict] = []
        self.coordinates_data: List[Tuple[float, float, float]] = []
        self.population_data: List[Dict] = []
        self.balance_data: List[Dict] = []
        self.chunk_data: List[Dict] = []
        
    def log(self, message: str):
        """Log messages with timestamp"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        
    def safe_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Make a safe HTTP request with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                self.log(f"HTTP {response.status_code} for {url}")
                return None
        except Exception as e:
            self.log(f"Request failed for {url}: {str(e)}")
            return None
        
    def scrape_wiki_nations(self):
        """Scrape nation data from Stoneworks Wiki"""
        self.log("Starting Wiki nations scraping...")
        
        # Get all nations from the category page
        nations_url = f"{self.wiki_base_url}/wiki/Category:Nations"
        response = self.safe_request(nations_url)
        
        if not response:
            self.log("Failed to fetch nations category page")
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all nation links
        nation_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/wiki/' in href and link.text and not any(skip in href.lower() for skip in ['category:', 'template:', 'file:']):
                if href.startswith('/'):
                    href = urljoin(self.wiki_base_url, href)
                nation_links.append((link.text.strip(), href))
                
        self.log(f"Found {len(nation_links)} potential nation pages")
        
        # Scrape individual nation pages
        for nation_name, nation_url in nation_links[:100]:  # Limit for testing
            try:
                nation_data = self.scrape_nation_page(nation_name, nation_url)
                if nation_data:
                    self.nations_data.append(nation_data)
                time.sleep(0.5)  # Be respectful to the server
            except Exception as e:
                self.log(f"Error scraping nation {nation_name}: {e}")
                
    def scrape_nation_page(self, nation_name: str, nation_url: str) -> Optional[Dict]:
        """Scrape individual nation page for data"""
        response = self.safe_request(nation_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        nation_data = {
            'name': nation_name,
            'url': nation_url,
            'population': self.extract_population(soup),
            'capital': self.extract_capital(soup),
            'leader': self.extract_leader(soup),
            'coordinates': self.extract_coordinates(soup),
            'cities': self.extract_cities(soup),
            'territory_size': self.extract_territory_size(soup),
            'founding_date': self.extract_founding_date(soup),
            'government_type': self.extract_government_type(soup)
        }
        
        return nation_data
        
    def extract_population(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract population from nation page"""
        patterns = [
            r'population[:\s]*(\d+)',
            r'citizens[:\s]*(\d+)',
            r'inhabitants[:\s]*(\d+)'
        ]
        
        text = soup.get_text().lower()
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
        
    def extract_capital(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract capital city from nation page"""
        patterns = [
            r'capital[:\s]*([^\n\r,]+)',
            r'capitol[:\s]*([^\n\r,]+)'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
        
    def extract_leader(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract leader/ruler from nation page"""
        patterns = [
            r'leader[:\s]*([^\n\r,]+)',
            r'ruler[:\s]*([^\n\r,]+)',
            r'king[:\s]*([^\n\r,]+)',
            r'president[:\s]*([^\n\r,]+)',
            r'emperor[:\s]*([^\n\r,]+)'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
        
    def extract_coordinates(self, soup: BeautifulSoup) -> List[Tuple[int, int]]:
        """Extract coordinates from nation page"""
        coords = []
        patterns = [
            r'(\-?\d+)[,\s]+(\-?\d+)',
            r'x[:\s]*(\-?\d+)[,\s]*z[:\s]*(\-?\d+)',
            r'coords?[:\s]*(\-?\d+)[,\s]*(\-?\d+)'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    x, z = int(match[0]), int(match[1])
                    coords.append((x, z))
                except ValueError:
                    continue
                    
        return coords
        
    def extract_cities(self, soup: BeautifulSoup) -> List[str]:
        """Extract cities/towns from nation page"""
        cities = []
        
        # Look for lists of cities
        for list_item in soup.find_all(['li', 'ul']):
            text = list_item.get_text().strip()
            if any(keyword in text.lower() for keyword in ['city', 'town', 'settlement']):
                # Extract city names
                city_matches = re.findall(r'([A-Z][a-zA-Z\s]+)', text)
                cities.extend([city.strip() for city in city_matches if len(city.strip()) > 2])
                
        return list(set(cities))  # Remove duplicates
        
    def extract_territory_size(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract territory/area information"""
        patterns = [
            r'area[:\s]*([^\n\r,]+)',
            r'territory[:\s]*([^\n\r,]+)',
            r'size[:\s]*([^\n\r,]+)',
            r'(\d+)\s*(?:chunks?|blocks?|km²?)'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
        
    def extract_founding_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract founding date"""
        patterns = [
            r'founded[:\s]*([^\n\r,]+)',
            r'established[:\s]*([^\n\r,]+)',
            r'created[:\s]*([^\n\r,]+)'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
        
    def extract_government_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract government type"""
        patterns = [
            r'government[:\s]*([^\n\r,]+)',
            r'(?:kingdom|republic|empire|federation|union|state)[^\n\r,]*'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0).strip()
        return None
        
    def scrape_census_data(self):
        """Scrape population census data"""
        self.log("Starting census data scraping...")
        
        census_urls = [
            f"{self.wiki_base_url}/wiki/Stoneworks_MC_Wiki:Rathnir_Public_Census_October_2020",
            f"{self.wiki_base_url}/wiki/Stoneworks_MC_Wiki:Rathnir_Public_Census_November_2020",
            f"{self.wiki_base_url}/wiki/Stoneworks_MC_Wiki:Rathnir_Public_Census_January_2021"
        ]
        
        for census_url in census_urls:
            response = self.safe_request(census_url)
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                census_data = self.parse_census_page(soup, census_url)
                self.population_data.extend(census_data)
                
    def parse_census_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Parse census page for population data"""
        data = []
        
        # Look for tables with population data
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    try:
                        nation_name = cells[0].get_text().strip()
                        population = cells[1].get_text().strip()
                        
                        # Try to extract number from population
                        pop_match = re.search(r'(\d+)', population)
                        if pop_match:
                            data.append({
                                'nation': nation_name,
                                'population': int(pop_match.group(1)),
                                'source': url,
                                'type': 'census'
                            })
                    except:
                        continue
                        
        return data
        
    def save_data_to_files(self):
        """Save all scraped data to files"""
        self.log("Saving data to files...")
        
        # Save coordinates
        if self.coordinates_data:
            with open('coordinates.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['X', 'Y', 'Z'])
                for x, y, z in self.coordinates_data:
                    writer.writerow([x, y, z])
            self.log(f"Saved {len(self.coordinates_data)} coordinates to coordinates.csv")
            
        # Save nations comprehensive data
        if self.nations_data:
            with open('nations_comprehensive.json', 'w') as f:
                json.dump(self.nations_data, f, indent=2)
            self.log(f"Saved {len(self.nations_data)} nations to nations_comprehensive.json")
            
        # Save territories data  
        if self.territories_data:
            with open('territories_data.json', 'w') as f:
                json.dump(self.territories_data, f, indent=2)
            self.log(f"Saved {len(self.territories_data)} territories to territories_data.json")
            
        # Save balances data
        if self.territories_data:
            with open('balances.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Territory', 'Nation', 'Balance', 'Level', 'Chunks'])
                for territory in self.territories_data:
                    writer.writerow([
                        territory['name'],
                        territory.get('nation_name', ''),
                        territory.get('balance', 0.0),
                        territory.get('level', ''),
                        territory.get('chunks', 0)
                    ])
            self.log(f"Saved balance data for {len(self.territories_data)} territories to balances.csv")
            
        # Save population data
        if self.territories_data:
            with open('population_detailed.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Territory', 'Nation', 'Player_Count', 'Players'])
                for territory in self.territories_data:
                    players_str = '; '.join(territory.get('players', []))
                    writer.writerow([
                        territory['name'],
                        territory.get('nation_name', ''),
                        territory.get('player_count', 0),
                        players_str
                    ])
            self.log(f"Saved detailed population data to population_detailed.csv")
            
        # Save chunk data
        if self.territories_data:
            with open('chunks_data.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Territory', 'Nation', 'Chunks', 'Territory_Area', 'Coordinates_Count'])
                for territory in self.territories_data:
                    writer.writerow([
                        territory['name'],
                        territory.get('nation_name', ''),
                        territory.get('chunks', 0),
                        territory.get('territory_area', 0),
                        territory.get('coordinate_count', 0)
                    ])
            self.log(f"Saved chunk data for {len(self.territories_data)} territories to chunks_data.csv")
            
        # Calculate totals and validate consistency
        total_balance = sum(t.get('balance', 0) for t in self.territories_data)
        total_chunks = sum(t.get('chunks', 0) for t in self.territories_data)
        total_players = sum(t.get('player_count', 0) for t in self.territories_data)
        unique_players = set()
        for t in self.territories_data:
            unique_players.update(t.get('players', []))
        
        # Validation checks
        coordinate_count_check = sum(t.get('coordinate_count', 0) for t in self.territories_data)
        
        summary = {
            'scraping_completed': time.strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'BlueMap Live Markers API',
            'total_coordinates': len(self.coordinates_data),
            'total_nations': len(self.nations_data),
            'total_territories': len(self.territories_data),
            'total_balance_server': total_balance,
            'total_chunks_server': total_chunks,
            'total_players_server': total_players,
            'unique_players_server': len(unique_players),
            'coordinate_validation': coordinate_count_check == len(self.coordinates_data),
            'files_created': [
                'coordinates.csv',
                'nations_comprehensive.json', 
                'territories_data.json',
                'balances.csv',
                'population_detailed.csv',
                'chunks_data.csv',
                'scraping_summary.json'
            ]
        }
        
        with open('scraping_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
            
        self.log("=== DATA SAVING COMPLETED ===")
        self.log(f"📊 FINAL STATISTICS:")
        self.log(f"  • {len(self.coordinates_data):,} coordinate points")
        self.log(f"  • {len(self.nations_data)} nations")
        self.log(f"  • {len(self.territories_data)} territories/cities")
        self.log(f"  • ${total_balance:,.2f} total server economy")
        self.log(f"  • {total_chunks:,} total claimed chunks")
        self.log(f"  • {total_players:,} total players")
        
    def scrape_bluemap_markers(self):
        """
        Scrape comprehensive data from BlueMap markers API, 
        handling duplicate territories by aggregating their data.
        """
        self.log("Starting BlueMap markers scraping...")
        
        response = self.safe_request(self.markers_url)
        if not response:
            self.log("Failed to fetch markers data")
            return
            
        try:
            markers_data = response.json()
            lands_data = markers_data.get("me.angeschossen.lands", {})
            markers = lands_data.get("markers", {})
            
            self.log(f"Found {len(markers)} potential territories/cities")
            
            # Use dictionaries to store unique territories and nations
            unique_territories: Dict[str, Dict] = {}
            nations_dict: Dict[str, Dict] = {}
            
            for marker_info in markers.values():
                territory_data = self.parse_territory_marker(marker_info)
                if not territory_data or not territory_data.get('name'):
                    continue
                
                territory_name = territory_data['name']
                
                # Deduplicate and aggregate territory data
                if territory_name not in unique_territories:
                    unique_territories[territory_name] = territory_data
                else:
                    # If the territory already exists, aggregate new data
                    existing_territory = unique_territories[territory_name]
                    existing_territory['chunks'] += territory_data.get('chunks', 0)
                    existing_territory['balance'] += territory_data.get('balance', 0)
                    existing_players = set(existing_territory.get('players', []))
                    new_players = set(territory_data.get('players', []))
                    combined_players = list(existing_players.union(new_players))
                    existing_territory['players'] = combined_players
                    existing_territory['player_count'] = len(combined_players)

                # Group by nation and aggregate data
                nation_name = territory_data.get('nation_name')
                if nation_name:
                    if nation_name not in nations_dict:
                        nations_dict[nation_name] = {
                            'name': nation_name,
                            'level': territory_data.get('nation_level'),
                            'capital': territory_data.get('nation_capital'),
                            'territories': set(), # Use a set for unique names
                            'total_chunks': 0,
                            'total_balance': 0.0,
                            'total_players': 0,
                            'all_players': set()
                        }
                    
                    nation = nations_dict[nation_name]
                    
                    # Only aggregate if this territory is new to the nation's set
                    if territory_name not in nation['territories']:
                        nation['territories'].add(territory_name)
                        nation['total_chunks'] += territory_data.get('chunks', 0)
                        nation['total_balance'] += territory_data.get('balance', 0.0)
                        nation['all_players'].update(territory_data.get('players', []))

                # Extract coordinates from shape and add to the main list
                if 'shape' in marker_info:
                    for coord in marker_info['shape']:
                        self.coordinates_data.append((coord['x'], coord.get('y', 62), coord['z']))

            # Finalize data from dictionaries to lists
            self.territories_data = list(unique_territories.values())
            
            # Convert nations dict to list and clean up player sets
            for nation_name, nation_data in nations_dict.items():
                nation_data['territories'] = list(nation_data['territories'])
                nation_data['unique_players'] = len(nation_data['all_players'])
                nation_data['all_players'] = list(nation_data['all_players'])
                self.nations_data.append(nation_data)
            
            self.log(f"Processed {len(self.territories_data)} unique territories")
            self.log(f"Processed {len(self.nations_data)} nations")
            self.log(f"Extracted {len(self.coordinates_data)} coordinate points")
            
        except Exception as e:
            self.log(f"Error parsing markers data: {e}")
            raise
            
    def parse_territory_marker(self, marker_info: Dict) -> Optional[Dict]:
        """Parse a single territory marker for all data"""
        try:
            # Extract basic info
            territory_name = marker_info.get('label', 'Unknown')
            position = marker_info.get('position', {})
            shape = marker_info.get('shape', [])
            detail = marker_info.get('detail', '')
            
            # Parse HTML detail for structured data
            soup = BeautifulSoup(detail, 'html.parser')
            detail_text = soup.get_text()
            
            # Extract key data using regex
            level_match = re.search(r'Level:\s*(\w+)', detail_text)
            balance_match = re.search(r'Balance:\s*\$([0-9,]+\.\d{2})', detail_text)
            chunks_match = re.search(r'Chunks:\s*(\d+)', detail_text)
            players_match = re.search(r'Players \((\d+)\):\s*([^<]+)', detail_text)
            nation_match = re.search(r'This land belongs to nation ([^:]+):', detail_text)
            
            # Parse nation information from the sub-section of the HTML
            nation_level_match = None
            nation_capital_match = None
            if nation_match:
                nation_detail_text = detail_text.split(nation_match.group(0))[-1]
                nation_level_match = re.search(r'Level:\s*(\w+)', nation_detail_text)
                nation_capital_match = re.search(r'Capital:\s*([^<\n]+)', nation_detail_text)
            
            # Parse balance
            balance = 0.0
            if balance_match:
                balance_str = balance_match.group(1).replace(',', '')
                balance = float(balance_str)
            
            # Parse player list
            players = []
            player_count = 0
            if players_match:
                player_count = int(players_match.group(1))
                players_str = players_match.group(2)
                # Split players by comma and clean up, stop at first "This land belongs"
                players_str_cleaned = players_str.split("This land belongs")[0]
                players = [p.strip() for p in players_str_cleaned.split(',') if p.strip()]
            
            # Calculate territory area from chunks (standardized)
            chunks = int(chunks_match.group(1)) if chunks_match else 0
            territory_area = chunks * 256  # 1 chunk = 16x16 = 256 blocks
            
            territory_data = {
                'name': territory_name,
                'position': position,
                'level': level_match.group(1) if level_match else None,
                'balance': balance,
                'chunks': chunks,
                'player_count': player_count,
                'players': players,
                'nation_name': nation_match.group(1).strip() if nation_match else None,
                'nation_level': nation_level_match.group(1) if nation_level_match else None,
                'nation_capital': nation_capital_match.group(1).strip() if nation_capital_match else None,
                'territory_area': territory_area,
                'shape_coordinates': shape,
                'coordinate_count': len(shape),
                'detail_html': detail
            }
            
            return territory_data
            
        except Exception as e:
            self.log(f"Error parsing territory marker: {e}")
            return None
            
    def calculate_polygon_area(self, shape: List[Dict]) -> float:
        """Calculate area of a polygon using shoelace formula"""
        if len(shape) < 3:
            return 0
            
        area = 0
        n = len(shape)
        
        for i in range(n):
            j = (i + 1) % n
            area += shape[i]['x'] * shape[j]['z']
            area -= shape[j]['x'] * shape[i]['z']
            
        return abs(area) / 2.0

    def run_full_scrape(self):
        """Run the complete scraping process"""
        self.log("Starting comprehensive Stoneworks data scraping...")
        
        try:
            # 1. Scrape BlueMap markers for live territory data
            self.scrape_bluemap_markers()
            
            # 2. Save all data
            self.save_data_to_files()
            
            self.log("=== SCRAPING COMPLETED SUCCESSFULLY ===")
            
        except Exception as e:
            self.log(f"Scraping failed with error: {e}")
            raise

def main():
    """Main function to run the scraper"""
    scraper = StoneworksDataScraper()
    scraper.run_full_scrape()

if __name__ == "__main__":
    main()
