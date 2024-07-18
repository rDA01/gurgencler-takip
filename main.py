import asyncio
import logging
import requests
from bs4 import BeautifulSoup
import threading

from data.entities.product import Product
from data.repositories.productRepository import ProductRepository
from service.productService import ProductService
from service.telegramService import TelegramService
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

class LoggingConfigurator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler('application.log')
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

class GatherPagesItems(LoggingConfigurator):
    def __init__(self, product_repo,url):
        self.base_url=url
        self.page_count=0
        self.item_count=0
        self.product_repo = product_repo

    async def gather_page_number(self, base_url):
        try:
            response = requests.get(base_url)
            if response.status_code == 200:

                PATH = "C:\Program Files (x86)\chromedriver.exe"
                options = webdriver.ChromeOptions()
                options.add_experimental_option("detach", True)
                cService = webdriver.ChromeService(executable_path=PATH)
                driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
                driver.get(base_url)
                time.sleep(5)
                button = driver.find_element(By.ID, "button-1580496494")
                button.click()
                time.sleep(5)
                
                for i in range(10):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    

                    i += 1
                    time.sleep(1)
                
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                divs = soup.find_all('div', class_='product-item-info')

                print(len(divs))
                
                for div in divs:
                    try:
                        container = div.find('div',class_='product details product-item-details eln-product-item-details')
                        details = container.find('a',class_="product-item-link")
                        prc_box_dscntd = container.find('div', class_='price-box price-final_price')
                    
                        prc_span = prc_box_dscntd.find('span', class_="price-container price-final_price tax weee")
                        span = prc_span.find('span',class_="price-wrapper")
                        price = span.find('p',class_="special-price")
                        p = price.find('span',class_="price")
                    except:
                        pass

                    if details and p:
                        title = details.get_text(strip=True)                       
                        href = details['href']
                                                
                        item =  self.product_repo.get_product_by_link(href)
                        price_text = p.text.strip()
                        price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                        price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))                        
                        
                        if item is False:


                            product = Product(id=None,title=title, link=href, price=price)
                            
                            self.product_repo.add_product(product)                    

                    else:
                        
                        print("Incomplete data found in div, skipping.")
                
          
            else:
                print("Failed to retrieve page:", response.status_code)
                return False
        except Exception as err:
            print("Error occurred:", err)
            return False
        
        return True

    async def gather_page_numbers(self):
        base_url = self.base_url
        
        await self.gather_page_number(base_url)

async def Main():
    product_repo = ProductRepository()

    smartphones = GatherPagesItems(product_repo,"https://www.gurgencler.com.tr/iphone?filters[quantity_and_stock_status]=yes")
    
    await smartphones.gather_page_numbers()

    
    telegram_service = TelegramService(bot_token='7393980187:AAGJHwoW6DY98jZOvTzdq0o7Ojt8X1VO28Q', chat_id='-1002203530212')

    productService = ProductService(product_repo, telegram_service)
    
    while True:
        await productService.updateProduct()
    

asyncio.run(Main())