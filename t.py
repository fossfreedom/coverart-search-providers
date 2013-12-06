
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import GObject

import time

main_loop = None

class CoverSearch(GObject.Object):
    
    __gsignals__ = {
        'connect': (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self):
        super(CoverSearch, self).__init__()
        #self.emit('connect')
        GObject.threads_init()
        user_data = 1
        print( "1st job push")
        Gio.io_scheduler_push_job(self.slow_stuff, 1, 
            GLib.PRIORITY_DEFAULT, None)
        print( "2nd job push")
        Gio.io_scheduler_push_job(self.slow_stuff, 2, 
            GLib.PRIORITY_DEFAULT, None)
        print ("finish init")
        
    def slow_stuff(self, job, cancellable, user_data):
        print ("source")
        #print (job)
        print (cancellable)
        print (user_data)
        time.sleep(5)
        #self.emit('connect')
        print ("end")
        return False
        
    def callback(self, result, user_data):
        print ("callback")
        
        print (user_data)
        self.emit('connect')
        
    def do_connect(self, *args):
        print ("here")
        main_loop.quit()
        
#main_loop.quit()

if __name__ == "__main__":
    main_loop = GLib.MainLoop()
    
    a = CoverSearch()
    
    main_loop.run()
