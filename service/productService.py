from decimal import Decimal
from data.repositories.productRepository import ProductRepository
from data.entities.product import Product

import requests
from bs4 import BeautifulSoup
import re

from service.telegramService import TelegramService

class ProductService:
    def __init__(self, repository: ProductRepository, telegram_service: TelegramService):
        self.repository = repository
        self.telegram_service = telegram_service
        self.base_url = "https://www.gurgencler.com.tr/"
    async def updateProduct(self):
        links = self.repository.get_all_product_links()

        for link in links:

            response = requests.get(str(link))
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                product_options_div = soup.find('div', class_='product-options-bottom')
                product_details = product_options_div.find('div',class_="mnm-after-final-price")
                product_detail_div = product_details.find('div',class_="price-box price-final_price")
                if product_detail_div:
                    span = product_detail_div.find('span',class_="normal-price")
                    span = span.find('span',class_="price-container price-final_price tax weee")
                    price_span = span.find('span', class_='price')
                    print(price_span)
                    if price_span:
                        
                        price_text = price_span.text.strip()
                        price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                        price_numeric = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))
                        price_numeric = Decimal(price_numeric)
                        product = self.repository.get_product_by_link(link)
                        print(product.title)
                        print("database: ",product.price)
                        print("web: ", price_numeric)
                        print(str(link))
                        if product:
                            if product.price != price_numeric:
                                print("existing price: ", product.price, '\n', "new price: ", price_numeric)
                                
                                old_price = Decimal(product.price)
                                
                                price_numeric = Decimal(price_numeric)
                                 
                                
                                product.price = Decimal(price_numeric)
                                self.repository.update_product(product)
                                isInstallment = Decimal(price_numeric) <= Decimal(old_price) * Decimal(0.92) 
                                if(isInstallment):
                                    print("installment catched, product link: ", product.link)
                                    installment_rate = ((old_price - Decimal(price_numeric)) / old_price) * 100
                                    old_price = "{:.2f}".format(old_price) 
                                    price_numeric = "{:.2f}".format(price_numeric)
                                    installment_rate = "{:.1f}".format(installment_rate)
                                    message = f"{str(link)} linkli, {product.title} başlıklı ürünün fiyatında indirim oldu. Önceki fiyat: {old_price}, Yeni fiyat: {price_numeric}. İndirim oranı: %{installment_rate}"

                                    await self.telegram_service.send_message(message)
                                   
                                
                            else:
                                print("Product price is remaining the same")
                        else:
                            print("Product not found in the database:", link)
                    else:
                        print("No price span found.")
                else:
                    print("Price box not found on the page:", link)
            else:
                print("Failed to retrieve page:", response.status_code)

        