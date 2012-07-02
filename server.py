from tornado.web import Application
from hello_shopply import HelloShopplyServiceHandler

import tornado.ioloop

API = Application([
            (r'/helloshopply', HelloShopplyServiceHandler),

        ],
    )
    
if __name__ == "__main__":
    API.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
