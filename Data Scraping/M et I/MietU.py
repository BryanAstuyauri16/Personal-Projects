from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import re

import time
import pandas as pd
import io
from collections import Counter
import numpy as np

from dash import Dash, dash_table, dcc, html, callback, clientside_callback
import pandas as pd
import dash_bootstrap_components as dbc

from dash.dependencies import State, Input, Output
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import warnings
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings(action="ignore"):
    fxn()

class Pharmacy_data():

    def __init__(self, url, product):
        self.url = url
        self.product = product

    def get_data(self):

        options = Options()
        options.add_argument('--headless=new')

        global wd
        wd = webdriver.Chrome(options=options)
        wd.get(self.url)
        wd.maximize_window()
        time.sleep(5)
        Product = self.product
        Search_input = wd.find_element(By.XPATH, '//input[contains(@placeholder, "Busca")]')
        Search_input.send_keys(Product, Keys.RETURN)
        time.sleep(5)

        SCROLL_PAUSE_TIME = 10
        last_height = wd.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = wd.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        Products = wd.find_elements(By.CSS_SELECTOR, 'div.col-12.col-sm-6.col-lg-4.col-xxl-3.mb-3.ng-star-inserted')
        df = pd.DataFrame() #Check inka 
        for product in Products:
            Product_name = product.find_element(By.CSS_SELECTOR, 'span.product-name.text').text
            Pharmacy = product.find_element(By.CSS_SELECTOR, 'span.ng-star-inserted').text
                
            try:
                Actual_price = float(product.find_element(By.CSS_SELECTOR, 'fp-product-price>p:nth-child(2)').get_attribute('innerText').split(' ')[1]) #I
            except Exception:
                try:
                    Actual_price = float(product.find_element(By.CSS_SELECTOR, 'fp-product-price-mifa div div span').get_attribute('innerText').split(' ')[1]) #M_2:3
                except:
                    Actual_price = float(product.find_element(By.CSS_SELECTOR, 'fp-product-regular-price-mifa div div span').get_attribute('innerText').split(' ')[1]) #M_1:2, 1:1 == regular_price

            try:
                Regular_price = float(product.find_element(By.CSS_SELECTOR, 'fp-product-regular-price.ng-star-inserted').get_attribute('innerText').split(' ')[1]) #I
            except Exception:
                try:
                    Regular_price = float(product.find_element(By.CSS_SELECTOR, 'fp-product-price>p:nth-child(2)').get_attribute('innerText').split(' ')[1]) #I
                except:
                    Regular_price = float(product.find_element(By.CSS_SELECTOR, 'fp-product-regular-price-mifa div div span').get_attribute('innerText').split(' ')[1]) #M_1:3
                    
            try:
                Price_dsct = float(product.find_element(By.CSS_SELECTOR, 'div.text-left.flex-grow-1').get_attribute('innerText').split(' ')[1]) #I
            except Exception:
                try:
                    Price_dsct = float(product.find_element(By.CSS_SELECTOR, 'fp-product-offer-price-mifa div div p').get_attribute('innerText').split(' ')[1]) # M_3:3
                except:
                    Price_dsct = np.nan #no importa

            Size = product.find_element(By.CSS_SELECTOR, 'span.text-tag').text
            row = pd.DataFrame(data= {'Product_name': [Product_name], 'Size': [Size], 'Pharmacy': [Pharmacy], 'Actual_price': [Actual_price], 'Regular_price': [Regular_price], 'Price_dsct': [Price_dsct]})
            df = pd.concat([df, row], axis = 0)
        df.reset_index(drop= True)
        wd.close()
        wd.quit()
        return df
    
df = pd.DataFrame()
load_figure_template(["minty", "minty_dark"])
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY, dbc.icons.FONT_AWESOME])

input_ = html.Div(
    children= [html.Div(id='container-button-basic', children='Enter a value and press submit:   \t'),
               dcc.Input(id= 'input_submit',
                         type= 'text',
                         placeholder= "Input a pharmacology"),
                         html.Button('Submit', id='submit-val', n_clicks=0)                         
    ],
    style=dict(display='flex', justifyContent='center'),
)

color_mode_switch =  html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
        dbc.Switch( id="color-mode-switch", value=False, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
    ]
)

table = html.Div([
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
        ],
        data=df.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=True,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size= 25,
        style_table={"overflowX": "auto",
                     'minWidth': '100%'},
        style_cell={
            'backgroundColor': 'rgb(255, 229, 204)',
            'color': 'black',
            'textOverflow': 'ellipsis',
            'overflow': 'hidden',
        },
        fill_width=False,
    ),
    dbc.Alert(id='tbl_out'),
]
)

app.layout = dbc.Container(
    [
        html.Div(
            children= ["Comparison between products in two different pharmacies"], 
            className="bg-primary text-white h3 p-2",
            style=dict(display='flex', justifyContent='center')),
        html.Div([input_, color_mode_switch]),
        table,
    ],
    fluid= True,
)

clientside_callback(
    """
    (switchOn) => {
       switchOn
         ? document.documentElement.setAttribute('data-bs-theme', 'light')
         : document.documentElement.setAttribute('data-bs-theme', 'dark')
       return window.dash_clientside.no_update
    }
    """,
    Output("color-mode-switch", "id"),
    Input("color-mode-switch", "value"),
)

@callback(
    [Output("datatable-interactivity", "data"), Output("datatable-interactivity", "columns"), Output("tbl_out", "children")],
    Input("submit-val", 'n_clicks'),
    State('input_submit', 'value'),
)

def Update_dataTable(n_clicks, product):
    if n_clicks > 0:
        inicio = time.time()
        product = str(product)
        url1 = 'https://www.mifarma.com.pe/'
        url2 = 'https://inkafarma.pe/'
        data_M = Pharmacy_data(url= url1, product= product).get_data()
        data_I = Pharmacy_data(url= url2, product= product).get_data()
        df = data_M.merge(data_I, on= ['Product_name', 'Size'], how='outer')
        df = df.rename(columns={'Product_name': 'Product Name', 'Pharmacy_x': 'Pharmacy', 'Actual_price_x': 'Actual Price', 'Regular_price_x': 'Regular Price', 'Price_dsct_x': 'Price dsct', 'Pharmacy_y': 'Pharmacy', 'Actual_price_y': 'Actual Price', 'Regular_price_y': 'Regular Price', 'Price_dsct_y': 'Price dsct'})
        columns=[
            {"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns
        ]
        fin = time.time()
        Alert = f"Your data has been updated. There are {df.index[-1]+1} element related to: {product}. The time taken was {fin-inicio} seconds"
        return df.to_dict('records'), columns, Alert
    else:
        pass

if __name__ == '__main__':
    app.run(debug=False, jupyter_mode="external")

