#!/usr/bin/python2
import dbus
import dbus.mainloop.glib
import gobject
import sys
import socket
import time
import logging

#from w1thermsensor import W1ThermSensor

from optparse import OptionParser

# proximity sensor readaout values
proxSensorsVal = [0, 0, 0, 0, 0]

# server ip and port
host = '192.168.43.150'
port = 4343

logger = logging.getLogger('colibot')

debug = False
counter = 0

SENSOR_THRESHOLD = 3300
DRIVE_DIST = 400
TURN_DIST = 180

def dbus_reply():
    pass


def dbus_error(e):
    # logger.info 'error %s'
    # logger.info str(e)
    pass


def control():
    # get the values of the sensors
    network.GetVariable("thymio-II", "prox.horizontal",
                        reply_handler=get_variables_reply, error_handler=get_variables_error)

    # send proximity sensor reading to colis
    reply = coli_com()

    if reply == 0:
        for i in range(0, DRIVE_DIST):
            network.SetVariable("thymio-II", "motor.left.target", [100])
            network.SetVariable("thymio-II", "motor.right.target", [100])

    if reply == 1:
        for i in range(0, TURN_DIST):
            network.SetVariable("thymio-II", "motor.left.target", [100])
            network.SetVariable("thymio-II", "motor.right.target", [-100])

        network.SetVariable("thymio-II", "motor.left.target", [0])
        network.SetVariable("thymio-II", "motor.right.target", [0])

    return True


def get_variables_reply(r):
    global proxSensorsVal
    proxSensorsVal = r


def get_variables_error(e):
    logger.info('error: ')
    logger.info(str(e))
    loop.quit()


def coli_com():
    global debug

    sum_prox = proxSensorsVal[0] + proxSensorsVal[1] + proxSensorsVal[2] + proxSensorsVal[3] + proxSensorsVal[4]
    sides = proxSensorsVal[0] + proxSensorsVal[4]

    global counter
    counter += 1
    if (counter % 2):
    # print("dirrrrty hack to take every second measurement only")
        return 6

    logger.info('# # # # # # # # # # # # # # # # #')
    logger.info('                         cycle {}'.format(counter/2))
    
    logger.info("Proximity sensor sum: " + str(sum_prox))


    try:
        if (sum_prox > SENSOR_THRESHOLD):
            logger.info("Obstacle detected!")
            if not debug:
                # send data to server
                s.sendto(str.encode('obstacle'), (host, port))
                logger.info("Sent 'obstacle' to reactor.")
            if debug == True:
                reply = 'turn' 
        else:
            logger.info("No obstacle")
            if not  debug:
                # send data to server
                s.sendto(str.encode('clear'), (host, port))
                logger.info("Sent 'clear' to reactor.")
            if debug == True:
                reply = 'drive' 


        if debug == False:
            # receive data
            d = s.recvfrom(1024)
            reply = d[0]
            addr = d[1]

        logger.info('Server reply : ' + str(reply))
#        logger.info('Executing ...')
        logger.info('                                #')
        logger.info('# # # # # # # # # # # # # # # # #')
        logger.info('')

        if (reply.decode("utf-8") == 'turn'):
#            s.sendto(str.encode('thanks'), (host, port))
            return 1
        if (reply.decode("utf-8") == 'drive'):
#            s.sendto(str.encode('thanks'), (host, port))            
            return 0
        else:
            return 6

    except socket.error as msg:
        logger.info('Error Code : ' + str(msg[0]) + ' Message ' + msg[1])


def cam_sync_at_start():
    network.SetVariable("thymio-II", "motor.left.target", [300])
    network.SetVariable("thymio-II", "motor.right.target", [300])
    time.sleep(1)
    network.SetVariable("thymio-II", "motor.left.target", [0])
    network.SetVariable("thymio-II", "motor.right.target", [0])    
    network.SetVariable("thymio-II", "motor.left.target", [-300])
    network.SetVariable("thymio-II", "motor.right.target", [-300])
    time.sleep(1)
    network.SetVariable("thymio-II", "motor.left.target", [0])
    network.SetVariable("thymio-II", "motor.right.target", [0]) 

if __name__ == '__main__':
    # format
    FORMAT = "[%(asctime)s ]   %(message)s"
    fileHandler = logging.FileHandler('log.txt')
    fileHandler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(fileHandler)
    logging.basicConfig(level=20, format=FORMAT, datefmt='%d.%m.%Y %H:%M:%S')
	

    parser = OptionParser()
    parser.add_option("-s", "--system", action="store_true", dest="system",
                      default=False, help="use the system bus instead of the session bus")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      default=False)

    (options, args) = parser.parse_args()	
	
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # use system bus instead of session bus if option is passed
    if options.system:
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()

    if options.debug:
        debug = True
    
    # Create Aseba network
    network = dbus.Interface(bus.get_object(
        'ch.epfl.mobots.Aseba', '/'), dbus_interface='ch.epfl.mobots.AsebaNetwork')

    # logger.info in the terminal the name of each Aseba NOde
    #logger.info(network.GetNodesList())

    # to sync camera:
    logger.info("cam-sync:")
    cam_sync_at_start()
    logger.info("Start logging")
    logger.info("###############################")
    logger.info("   ColiBot Thymio controller   ")
    logger.info("-------------------------------")
    logger.info("...        starting:        ...")


    # create dgram udp socket
    try:
        logger.info("Creating socket.")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        logger.info('Failed to create socket')
        sys.exit()



    # GObject loop
    # logger.info 'starting loop'
    loop = gobject.MainLoop()
    # call the callback of control flow
    handle = gobject.timeout_add(1000, control)  # every 0.1 sec
    loop.run()