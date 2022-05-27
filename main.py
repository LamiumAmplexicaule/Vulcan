import re
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from models import SearchIn, SearchOut, SearchSite

app = FastAPI()

origins = [
    "http://localhost",
    "https://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=False), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            "title": "Vulcan",
        },
    )


def num(string):
    return int(re.sub("\\D", "", string))


def path(string):
    parse = urlparse(string)
    query = parse.query
    path_plus = parse.path
    if len(query) > 0:
        path_plus += '?' + query
    return path_plus


def get_products(html, product_list_css_selector, products_css_selector):
    soup = BeautifulSoup(html, 'html.parser')
    product_list = soup.select_one(product_list_css_selector)
    if product_list is None:
        products = None
    else:
        products = product_list.select(products_css_selector)
    return products


@app.post("/search", response_model=SearchOut)
async def search(search_in: SearchIn):
    if search_in.site == SearchSite.AMAZON:
        url = 'https://www.amazon.co.jp/s?k=' + quote(search_in.value)
    elif search_in.site == SearchSite.YODOBASHI:
        url = 'https://www.yodobashi.com/?word=' + quote(search_in.value)
    elif search_in.site == SearchSite.FACTORY_GEAR:
        url = 'https://ec.f-gear.co.jp/item_list.html?keyword=' + quote(search_in.value)
    elif search_in.site == SearchSite.EHIME_MACHINE:
        url = 'https://ems-tools.jp/search?q=' + quote(search_in.value)
    elif search_in.site == SearchSite.WIT:
        url = 'https://www.worldimporttools.co.jp/p/search?keyword=' + quote(search_in.value)
    else:
        url = ''

    search_dict = search_in.dict()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:99.0) Gecko/20100101 Firefox/99.0',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    response = requests.get(url, headers=headers)
    html = response.text
    if response.status_code == 200:
        if search_in.site == SearchSite.AMAZON:
            product_list_css_selector = '.s-main-slot'
            products_css_selector = '.s-result-item'
            price_css_selector = 'div.s-price-instructions-style > div > a > span:nth-child(1) > span.a-offscreen'
            link_css_selector = 'h2.a-size-mini > a'
            products = get_products(html, product_list_css_selector, products_css_selector)
            if products is None:
                result = []
            else:
                result = [
                    (
                        f"<a href=https://www.amazon.co.jp{path(a.get('href'))} target='_blank' rel='noopener noreferrer'>{a.get_text().replace('　', ' ').strip()}</a>",
                        f"¥{num(price.get_text()):,}"
                    ) for product in products if
                    product.has_attr('data-uuid') and (a := product.select_one(link_css_selector)) is not None and (
                        price := product.select_one(price_css_selector)) is not None
                ]
        elif search_in.site == SearchSite.YODOBASHI:
            product_list_css_selector = '.srcResultItem'
            products_css_selector = '.srcResultItem_block'
            price_css_selector = 'span.productPrice'
            point_css_selector = 'span.goldPoint'
            link_css_selector = 'a.js_productListPostTag'
            products = get_products(html, product_list_css_selector, products_css_selector)
            if products is None:
                result = []
            else:
                result = [
                    (
                        f"<a href=https://www.yodobashi.com{path(a.get('href'))} target='_blank' rel='noopener noreferrer'>{a.get_text().replace('　', ' ').strip()}</a>",
                        f"¥{num(price.get_text()):,}, ¥{num(price.get_text()) - num(re.sub('（.+?）', '', product.select_one(point_css_selector).get_text())):,}"
                    ) for product in products if
                    (a := product.select_one(link_css_selector)) is not None and (
                        price := product.select_one(price_css_selector)) is not None
                ]
        elif search_in.site == SearchSite.FACTORY_GEAR:
            product_list_css_selector = '#itemListImage'
            products_css_selector = '.box'
            price_css_selector = 'span.teika > span'
            link_css_selector = '.text > h3 > span > a'
            products = get_products(html, product_list_css_selector, products_css_selector)
            if products is None:
                result = []
            else:
                result = [
                    (
                        f"<a href=https://ec.f-gear.co.jp{path(a.get('href'))} target='_blank' rel='noopener noreferrer'>{a.get_text().replace('　', ' ').strip()}</a>",
                        f"¥{num(price.get_text()):,}"
                    ) for product in products if (a := product.select_one(link_css_selector)) is not None and (
                        price := product.select_one(price_css_selector)) is not None
                ]
        elif search_in.site == SearchSite.EHIME_MACHINE:
            product_list_css_selector = '.product-list'
            products_css_selector = '.product-item'
            price_css_selector = 'span.price--highlight'
            link_css_selector = 'a.product-item__title'
            products = get_products(html, product_list_css_selector, products_css_selector)
            if products is None:
                result = []
            else:
                result = [
                    (
                        f"<a href=https://ems-tools.jp{path(a.get('href'))} target='_blank' rel='noopener noreferrer'>{a.get_text().replace('　', ' ').strip()}</a>",
                        f"¥{num(price.get_text()):,}"
                    ) for product in products if (a := product.select_one(link_css_selector)) is not None and (
                        price := product.select_one(price_css_selector)) is not None
                ]
        elif search_in.site == SearchSite.WIT:
            product_list_css_selector = '.fs-c-productList__list'
            products_css_selector = '.fs-c-productListItem'
            price_css_selector = '.fs-c-productPrice--selling > span > span > .fs-c-price__value'
            link_css_selector = 'h2.fs-c-productName > a'
            products = get_products(html, product_list_css_selector, products_css_selector)
            if products is None:
                result = []
            else:
                result = [
                    (
                        f"<a href=https://www.worldimporttools.co.jp{path(a.get('href'))} target='_blank' rel='noopener noreferrer'>{a.get_text().replace('　', ' ').strip()}</a>",
                        f"¥{num(price.get_text()):,}"
                    ) for product in products if
                    (a := product.select_one(link_css_selector)) is not None and (
                        price := product.select_one(price_css_selector)) is not None
                ]
        else:
            result = []

        search_dict.update({"result": result})
    return search_dict
