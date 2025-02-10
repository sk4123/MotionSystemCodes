import modules.spincam_v3 as spincam
import imageio
import time


class Camera:

    #Camera Properties

    global __EXPOSURE_MAX
    global __EXPOSURE_MIN
    global __EXPOSURE
    global __FPS_MAX
    global __FPS_MIN
    global __FPS
    global __GAIN_MIN
    global __GAIN_MAX
    global __STREAM
    global __PWD_FREQ
    global __CAMERA_ACQUISITION_INTERVAL
    global __INITIAL_FOLDER
    global FPSVar
    global ExpVar
    global AcqIntVar


    __FPS_MIN = 1
    __FPS_MAX = 30
    __FPS = 0
    __GAIN_MIN = 0
    __GAIN_MAX = 47  # Units are dB
    __EXPOSURE_MIN = 0.006  # microseconds
    __EXPOSURE_MAX = 200000  # microseconds seconds
    __EXPOSURE = __EXPOSURE_MAX
    __STREAM = False
    __PWD_FREQ = 640#hz
    __CAMERA_ACQUISITION_INTERVAL = 1 #secs

    FPSVar = __FPS
    AcqIntVar = __CAMERA_ACQUISITION_INTERVAL
    ExpVar = 0


    __INITIAL_FOLDER  = "SaveImages/"


    def find_and_init_cam(self):
        # Finds and initializes camera
        print('Connecting camera...')
        spincam.find_cam('test')

        spincam.init_cam()
        spincam.disable_auto_exp()
        spincam.disable_auto_gain()
        spincam.disable_auto_frame()
        spincam.enable_frame_rate_control()
        ExpVar = spincam.get_exp()/1000
        __FPS_MIN = spincam.get_fps_min()
        __FPS_MAX = spincam.get_fps_max()
        __FPS = spincam.get_frame_rate()
        print("FPS : {:.2f}".format(__FPS))
        __EXPOSURE_MIN = spincam.get_exp_min()
        __EXPOSURE_MAX = 1/__FPS*1000
        print("Exp. Max : {:.2f}".format(__EXPOSURE_MAX))
        spincam.set_exposure(__EXPOSURE_MAX*1000)
        __EXPOSURE  = __EXPOSURE_MAX
        self.init_gain(0)
        spincam.set_video_mode('7')
        #	ledserial.connect(__COM_PORT)
        
    def init_gain(self, gain):
        # gain text callback

        # Set gain for camera
        print('Initializing Gain to ' + str(gain))
        spincam.set_gain(gain)

    def set_FPS(self, fps):
        newFPS = fps
        nearestInteger = round(__PWD_FREQ/newFPS)
        print(nearestInteger)
        newFPS =  __PWD_FREQ/nearestInteger
        if newFPS>__FPS_MIN and newFPS<__FPS_MAX:
            __EXPOSURE_MAX = 1/newFPS*1000
            spincam.set_exposure(__EXPOSURE_MAX*1000)
            __EXPOSURE = __EXPOSURE_MAX
            ExpVar = (__EXPOSURE_MAX)
            spincam.set_frame_rate(newFPS)
            FPSVar = (newFPS)
        elif newFPS<__FPS_MIN:
            __EXPOSURE_MAX = 1/__FPS_MIN*1000
            spincam.set_exposure(__EXPOSURE_MAX*1000)
            __EXPOSURE = __EXPOSURE_MAX
            ExpVar = (__EXPOSURE_MAX)
            spincam.set_frame_rate(__FPS_MIN)
            FPSVar = __FPS_MIN
        elif newFPS>__FPS_MAX:
            __EXPOSURE_MAX = 1/__FPS_MAX*1000
            spincam.set_exposure(__EXPOSURE_MAX*1000)
            __EXPOSURE = __EXPOSURE_MAX
            ExpVar = (__EXPOSURE_MAX)
            spincam.set_frame_rate(__FPS_MAX)
            FPSVar = (__FPS_MAX)
        else:
            print("Enter a valid FPS")
            return False

    def set_exposure(self, exp):
        newExp = exp
        if newExp<=__EXPOSURE_MAX:
            spincam.set_exposure(newExp*1000)
        else:
            print("Cannot update the exposure time")
            return False
        
    def setAcquisitionInterval(self, acq):
        __CAMERA_ACQUISITION_INTERVAL = acq
        print("Acquisition Interval is set to {:.2f} seconds".format(__CAMERA_ACQUISITION_INTERVAL))

    def stop_stream(self):
        # Stops stream of cameras
        # Make sure they're streaming
        if __STREAM:
            print('Stopping stream...')

            # Stop acquisition
            spincam.end_acquisition()
            # End stream
            __STREAM = False

    def start_stream(self):
        # Starts stream of cameras
        # Ensure aren't already streaming
        if not __STREAM:
            print('Starting stream...')

            # Set buffer to newest only
            spincam.cam_node_cmd('TLStream.StreamBufferHandlingMode',
                                'SetValue',
                                'RW',
                                'PySpin.StreamBufferHandlingMode_NewestOnly')

            # Set acquisition mode to continuous
            spincam.cam_node_cmd('AcquisitionMode',
                                'SetValue',
                                'RW',
                                'PySpin.AcquisitionMode_Continuous')

            # Start acquisition
            spincam.start_acquisition()

            # Enable stream
            __STREAM = True

'''
    def mainAcquisition(self):

        if (__STREAM):
            self.stop_stream()
        time.sleep(0.1)
        self.start_stream()
        time.sleep(0.1)
        noOfLeds = len(__LED_DICT['IntesityValues'])
        TotalFramesInAcq = int(round(__CAMERA_ACQUISITION_INTERVAL * __FPS))
        NoOfOneLEDAcqFrame = int(round(TotalFramesInAcq/noOfLeds))
        Led.turnOffAllLEDs()
        while not __stop_event.is_set():
            for i in range(noOfLeds):
                t1 = time.time()
                Led.turnOnLED(__LED_DICT['LEDOrder'][i], __LED_DICT['IntesityValues'][i]/100)
                if i==noOfLeds-1:
                    data = spincam.get_image_and_return_array(TotalFramesInAcq-(noOfLeds-1)*(NoOfOneLEDAcqFrame))
                    __image_queue.put(data['data'])
                    __LEDName_queue.put(__LED_DICT['LEDOrder'][i])
                    t2 = time.time()
                    print("total {:01d} Acquisition took {:.03f} miliseconds".format(__LED_DICT['LEDOrder'][i], (t2-t1)*1000))
                    Led.turnOffLED(__LED_DICT['LEDOrder'][i])
                    continue
                data = spincam.get_image_and_return_array(NoOfOneLEDAcqFrame)
                __image_queue.put(data['data'])
                __LEDName_queue.put(__LED_DICT['LEDOrder'][i])
                t2 = time.time()
                print("total {:01d} Acquisition took {:.03f} miliseconds".format(__LED_DICT['LEDOrder'][i], (t2-t1)*1000))
                Led.turnOffLED(__LED_DICT['LEDOrder'][i])
'''

