import csv
import time

import requests
from bs4 import BeautifulSoup


def get_page_content(page_number):
    """
    Fetches the HTML content for a specific page number.

    Args:
        page_number (int): The page number to fetch

    Returns:
        BeautifulSoup object or None if error/404
    """
    base_url = "https://redsevillasingluten.org/category/establecimientos-de-la-red/"

    # Construct URL based on page number
    if page_number == 1:
        url = base_url
    else:
        url = f"{base_url}page/{page_number}/"

    print(f"Fetching page {page_number}: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')

    except requests.RequestException as e:
        print(f"Error fetching page {page_number}: {e}")
        return None


def extract_business_from_article(article):
    """
    Extracts business name and address from a single article element.

    Args:
        article: BeautifulSoup article element

    Returns:
        dict with 'Name' and 'Address' or None if extraction fails
    """
    # Extract business name from heading
    title_element = article.find(['h2', 'h3'])
    if not title_element:
        return None

    title_link = title_element.find('a')
    business_name = title_link.text.strip() if title_link else title_element.text.strip()

    if not business_name:
        return None

    # Extract address - look for p element in the nested divs
    address = ""

    # Try to find p elements within the article structure
    # Following the pattern: article > .mask > .tipi-xs-6.pegado > .textof > p
    p_elements = article.find_all('p')

    for p in p_elements:
        # Check if this p is within the expected div structure
        parent = p.parent
        if parent and ('textof' in parent.get('class', []) or
                      'entry-content' in parent.get('class', []) or
                      'entry-summary' in parent.get('class', [])):
            # Get the first line of the p element
            text = p.text.strip()
            if text:
                # Take only the first line
                first_line = text.split('\n')[0].strip()
                if first_line:
                    address = first_line
                    break

    return {
        'Name': business_name,
        'Address': address
    }


def scrape_all_pages():
    """
    Main scraping function that iterates through all pages.

    Returns:
        list of dictionaries containing business data
    """
    businesses = []
    page = 1
    max_empty_pages = 2  # Stop after 2 consecutive empty pages
    empty_page_count = 0

    while True:
        soup = get_page_content(page)

        if soup is None:
            print(f"No content found for page {page}")
            break

        # Find all articles on the page
        articles = soup.find_all('article')

        if not articles:
            empty_page_count += 1
            if empty_page_count >= max_empty_pages:
                print(f"No more articles after {max_empty_pages} empty pages")
                break
        else:
            empty_page_count = 0

            for article in articles:
                business_data = extract_business_from_article(article)
                if business_data:
                    businesses.append(business_data)
                    print(
                        f"  Found: {business_data['Name']} - "
                        f"{business_data['Address'] if business_data['Address'] else 'No address'}"
                    )

        page += 1

        # Be respectful with requests
        time.sleep(2)

    return businesses


def save_to_csv(businesses, filename='businesses.csv'):
    """
    Saves the business data to a CSV file.

    Args:
        businesses (list): List of business dictionaries
        filename (str): Output CSV filename
    """
    if not businesses:
        print("No businesses to save")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Address']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for business in businesses:
            writer.writerow(business)

    print(f"\nSaved {len(businesses)} businesses to {filename}")


def main():
    """
    Main execution function.
    """
    print("Starting web scraper for Red Sevilla Sin Gluten...")

    # Scrape all pages
    businesses = scrape_all_pages()

    # Save results to CSV
    save_to_csv(businesses)

    # Display summary
    print(f"\nTotal businesses scraped: {len(businesses)}")
    if businesses and len(businesses) > 0:
        print("\nFirst 5 businesses:")
        for i, business in enumerate(businesses[:5], 1):
            print(f"{i}. {business['Name']}")
            print(f"   Address: {business['Address'] if business['Address'] else 'Not found'}")


if __name__ == "__main__":
    main()
