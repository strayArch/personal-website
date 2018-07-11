from __future__ import absolute_import
from __future__ import print_function
import hashlib
import os
import tornado.ioloop
import tornado.web
from . import cfg

__all__ = ['main']


def _get_content_type(path):
    _match = cfg.EXT.search(path)
    if _match:
        return cfg.CONTENT[_match.group(1)]
    else:
        # Generally, default behavior would be an octet-stream but the auto-download behavior
        # is not desired. So let the default behavior be plain/text
        return cfg.CONTENT['text']


class StaticHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        etags = ("js/app", "css/app", "partial")
        if path.startswith(etags):
            # For static assets, set client cacheable and max-age of one week
            self.set_header("Cache-Control", "private,max-age=604800,must-revalidate")  # one week
        else:
            # For public assets, prevent caching
            self.set_header("Cache-Control", "no-cache,no-store,must-revalidate")
            content_type = _get_content_type(path)
            self.set_header("Content-Type", content_type)
        self.set_header("X-Frame-Options", "deny")
        self.set_header("X-XSS-Protection", "1; mode=block")
        self.set_header("X-Content-Type-Options", "nosniff")


class BaseHandler(tornado.web.RequestHandler):
    """Initialize hrefs and use the file hash for each files version"""
    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        self._partials = BaseHandler._get_hrefs("partial")
        self._css_files = BaseHandler._get_hrefs("css")
        self._js_files = BaseHandler._get_hrefs("js")

    @staticmethod
    def _get_file_hash(dir_key, fname):
        """Returns sha224 hash of file for cache busting purposes"""
        fabspath = os.path.join(cfg.DIR[dir_key], fname)
        with open(fabspath, "r") as fhandle:
            fhash = hashlib.sha224(fhandle.read()).hexdigest()
        return fhash

    @staticmethod
    def _get_hrefs(dir_key, order=None):
        hrefs = []
        flist = sorted(os.listdir(cfg.DIR[dir_key]))
        for fname in flist:
            fhash = BaseHandler._get_file_hash(dir_key, fname)
            href = "//{}/static/{}/{}?v={}".format(cfg.HOST, dir_key, fname, fhash)
            hrefs.append(href)
        return hrefs


class HomeHandler(BaseHandler):
    def get(self, *args):
        home_render_kwargs = {"partials": self._partials,
                              "css_files": self._css_files,
                              "js_files": self._js_files}
        self.render("index.html", **home_render_kwargs)


class PortfolioHandler(BaseHandler):
    def get(self, *args):
        portfolio_render_kwargs = {"partials": self._partials,
                                   "css_files": self._css_files,
                                   "js_files": self._js_files}
        self.render("index.html", **portfolio_render_kwargs)


class AboutMeHandler(BaseHandler):
    def get(self, *args):
        aboutme_render_kwargs = {"partials": self._partials,
                                 "css_files": self._css_files,
                                 "js_files": self._js_files}
        self.render("index.html", **aboutme_render_kwargs)


def main():
    handlers = [(r"/?(?:home/?)?", HomeHandler),
                (r"/portfolio/?(.*)?", PortfolioHandler),
                (r"/about-me/?", AboutMeHandler),
                (r"/static/(.*)", StaticHandler),
                (r"/public/(.*)", StaticHandler, {"path": cfg.DIR['public']})]
    _app = tornado.web.Application(handlers, **cfg.SETTINGS)
    _app.listen(cfg.PORT, address=cfg.ADDRESS)
    tornado.ioloop.IOLoop.current().start()
