from tornado.web import Application
from hello_shopply import HelloShopplyServiceHandler

API = Application([
            (r'/helloshopply', HelloShopplyServiceHandler),

        ],
    )
