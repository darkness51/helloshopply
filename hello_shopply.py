from hello_es import Model
import tornado.web

class HelloShopplyServiceHandler(tornado.web.RequestHandler):

    def get(self):
        model = Model()
        self.set_header('Content-Type', 'application/json')
        self.write(model.get_message().get("allinfo"))    
