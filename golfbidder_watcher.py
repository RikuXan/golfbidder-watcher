import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
from os import environ


watches = json.loads(environ.get('GOLFBIDDER_WATCHES', '[]'))


def get_all_products(urls):
    products = []

    for url in urls:
        if '/SearchResults' in url:
            search_page = BeautifulSoup(requests.get(url).text, features='html.parser')
            model_urls = [urljoin(url, model_block.find('a')['href']) for model_block in search_page.find_all('div', {'class': 'gallery-item-content'})]
            products.extend(get_all_products(model_urls))
        elif '/models/' in url:
            model_page = BeautifulSoup(requests.get(url).text, features='html.parser')
            model_blocks = model_page.find_all('div', {'class': 'col-info-cell'})[1:]
            for model_block in model_blocks:
                product_base = {
                    'product_name': model_block.find('div', {'class': 'col-model'}).find('h3', {'class': 'product-name'}).find('a').text,
                    'price': float(f"{model_block.find('div', {'class': 'col-price'}).find('span', {'class': 'integer-part'}).text}.{model_block.find('div', {'class': 'col-price'}).find('span', {'class': 'decimal-part'}).text[1:-2]}"),
                    'url': urljoin(url, model_block.find('div', {'class': 'col-model'}).find('h3', {'class': 'product-name'}).find('a')['href'])
                }
                product_attributes = {
                    attribute_block.find('label', {'class': 'attribute-label'}).text: attribute_block.find('span', {'class': 'attribute-value'}).text
                    for attribute_block in model_block.find('div', {'class': 'col-model'}).find_all('p', {'class': 'attribute'})
                }

                products.append({**product_base, **product_attributes})
        else:
            print(f"Ignoring invalid URL: {url}")

    return products


def watch_golfbidder():
    while True:
        for watch in watches:
            products = get_all_products(watch['urls'])
            print(f"Found {len(products)} products for watch {watch['name']}")

            any_product_found = False
            for product in products:
                matches_conditions = True
                for condition in watch['conditions']:
                    if condition['type'] == 'attribute':
                        if condition['label'] in product:
                            if product[condition['label']] not in condition['values']:
                                matches_conditions = False
                                break
                    elif condition['type'] == 'max_price':
                        if product['price'] > condition['value']:
                            matches_conditions = False
                            break

                if matches_conditions:
                    print(f"Found product matching conditions: {product['url']}")
                    any_product_found = True

            if not any_product_found:
                print("Found no products matching conditions")

        time.sleep(int(environ.get('SLEEP_INTERVAL', '60')))


if __name__ == '__main__':
    watch_golfbidder()
