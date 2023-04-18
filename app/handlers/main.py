# !/usr/bin/env python3

from handlers.base import BaseHandler
from tornado.web import authenticated
from json import dumps


class MainHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('main.html', xsrf=self.xsrf_token)


class ActivitiesPageHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('activities.html')


class AddActivityPageHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('add-activity.html')


class AttachFilesPageHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('attach-files.html')


class EditActivityPageHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('edit-activity.html')


class TimelineHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('timeline.html')


# class AppendFileTplHandler(BaseHandler):

#     @authenticated
#     def get(self):
#         self.render('append-file.tpl.html')


class Appconfig(BaseHandler):

    def get(self):
        api_settings = {
            'domain': self.settings['ROOT_DOMAIN'],
            'authcenter': self.settings['AUTHCENTER'],
            'user_manager': self.settings['USMANAGER'],
            'dash_app': self.settings['DASHBOARD'],
            'main_app': self.settings['APPURL'],
            'admin': self.settings['USMANAGER'] + '/#/admin',
            'images': self.settings['URL_IMAGES'] + '/static/images/',
        }

        self.set_status(200)
        self.set_header(
            'Content-Type', 'application/javascript; charset=UTF-8')
        variavel = 'var api_settings = %s;' % (dumps(api_settings))
        self.finish(variavel)
