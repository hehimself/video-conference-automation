import random
import time
from pywinauto import application
from pywinauto.findwindows import WindowAmbiguousError, WindowNotFoundError

APPS_POOL = ['Chrome', 'GVIM', 'Notepad', 'Calculator', 'SourceTree', 'Outlook']


# Select random app from the pull of apps
def show_rand_app():
    # Init App object
    app = application.Application()

    random_app = random.choice(APPS_POOL)
    try:
        app.connect(title_re="Teams")

        # Access app's window object
        app_dialog = app.top_window()

        app_dialog.minimize()
        app_dialog.restore()
        #app_dialog.SetFocus()
    except(WindowNotFoundError):
        # print '"%s" not found' % random_app
        pass
    except(WindowAmbiguousError):
        # print 'There are too many "%s" windows found' % random_app
        pass

for i in range(5):
    show_rand_app()
    time.sleep(0.3)