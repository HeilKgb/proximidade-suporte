# !/usr/bin/env python3

from handlers.base import VersionHandler
from handlers.auth import LogoutHandler
from handlers.auth import UserInfoHandler
from handlers.auth import UserRole
from handlers.main import MainHandler
from handlers.main import ActivitiesPageHandler
from handlers.main import AddActivityPageHandler
from handlers.main import AttachFilesPageHandler
from handlers.main import EditActivityPageHandler
# from handlers.main import AppendFileTplHandler
from handlers.main import TimelineHandler
from handlers.main import Appconfig
from handlers.api import ActivitiesHandler
from handlers.api import ApplicationsHandler
from handlers.api import OrganizationsHandler
from handlers.api import FilesUploadHandler
from handlers.api import CrossActivitiesHandler
from handlers.webhook import WebHooksCallbackHandler

# Defining routes
url_patterns = [
    # API
    (r"/activities/?$", ActivitiesHandler),
    (r"/activities/(.*)/?$", ActivitiesHandler),
    (r"/applications/?$", ApplicationsHandler),
    (r"/organizations/?$", OrganizationsHandler),
    (r"/files/upload", FilesUploadHandler),
    # API Trello
    (r"/trello/webhooks/?$", WebHooksCallbackHandler),
    (r"/trello/webhooks/(\w+)/?$", WebHooksCallbackHandler),
    # (r"/entities/(\w+)/?$", EntitiesHandler),
    # Cross
    (r"/cross/activities/?$", CrossActivitiesHandler),

    # Web Pages
    (r"/", MainHandler),
    (r'/version/?', VersionHandler),
    (r"/application-config.js", Appconfig),
    (r"/activities.html", ActivitiesPageHandler),
    (r"/add-activity.html", AddActivityPageHandler),
    (r"/attach-files.html", AttachFilesPageHandler),
    (r"/edit-activity.html", EditActivityPageHandler),
    # (r"/append-file.tpl.html", AppendFileTplHandler),
    (r"/timeline.html", TimelineHandler),

    # AUTH
    (r"/auth/logout", LogoutHandler),
    (r"/auth/user/info", UserInfoHandler),
    # Get User roles
    ("/auth/user/role?$", UserRole)
]
