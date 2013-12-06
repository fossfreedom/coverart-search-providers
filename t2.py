from gi.repository import GLib, Gio, GObject
import time

def slow_stuff(job, cancellable, user_data):
    print "Slow!"
    for i in xrange(5):
        print "doing slow stuff..."
        time.sleep(0.5)
    print "finished doing slow stuff!"
    return False # job completed

def main():
    GObject.threads_init()
    print "Starting..."
    Gio.io_scheduler_push_job(slow_stuff, None, GLib.PRIORITY_DEFAULT, None)
    print "It's running async..."
    GLib.idle_add(ui_stuff)
    GLib.MainLoop().run()

def ui_stuff():
    print "This is the UI doing stuff..."
    time.sleep(1)
    return True

if __name__ == '__main__':
    main()
