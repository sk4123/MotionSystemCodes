import os
import atexit
from warnings import warn
from contextlib import suppress
from datetime import datetime
import PySpin
import numpy as np
import numpy.matlib 
import cv2 
import time


__SYSTEM = PySpin.System.GetInstance()

__CAM = None

def __destructor():
    print('Cleaning up SpinCam...')

    # Cleanup
    __cleanup_cam()

    if __SYSTEM.IsInUse():
        print('System is still in use')


atexit.register(__destructor)

def __createPolMask_stack(z, height, width):
    u0 = np.array([ [1,0], [0,0] ])
    u45 = np.array([ [0,1], [0,0] ])
    u90 = np.array([ [0,0], [0,1] ])
    u135 = np.array([ [0,0], [1,0] ])
    c0 = np.matlib.repmat(u0,int(height/2),int(width/2))
    c90 = np.matlib.repmat(u90,int(height/2),int(width/2))
    c45 = np.matlib.repmat(u45,int(height/2),int(width/2))
    c135 = np.matlib.repmat(u135,int(height/2),int(width/2))
    c0 = np.reshape(c0, (1, height, width))
    c90 = np.reshape(c90, (1, height, width))
    c45 = np.reshape(c45, (1, height, width))
    c135 = np.reshape(c135, (1, height, width))
    c0 = np.repeat(c0,z,0)
    c90 = np.repeat(c90,z,0)
    c135 = np.repeat(c135,z,0)
    c45 = np.repeat(c45,z,0)
    return [c0, c45, c90, c135]

def __createRGBMask(height, width):
    uR = np.array([ [1,0], [0,0] ])
    uG = np.array([ [0,1], [1,0] ])
    uB = np.array([ [0,0], [0,1] ])
    cB = np.matlib.repmat(uB,int(height/2),int(width/2))
    cG = np.matlib.repmat(uG,int(height/2),int(width/2))
    cR = np.matlib.repmat(uR,int(height/2),int(width/2))
    return [cR, cG, cB]

def __NormalizeImages(source, LUT_red, LUT_green, LUT_blue):
	[cR,cG,cB] = __createRGBMask(source.shape[0],source.shape[1])
	hist = cv2.calcHist([source], [0], np.uint8(cR), [2**16], [0,2**16])
	maxCR = np.argmax(hist)
    
	LUT_red_blue = np.float32(LUT_red * maxCR * cB)
	LUT_red_green = np.float32(LUT_red * maxCR * cG)
    
	hist = cv2.calcHist([source], [0], np.uint8(cB), [2**16], [0,2**16])
	maxCB = np.argmax(hist)
    
	LUT_blue_red = np.float32(LUT_blue * maxCB * cR)
	LUT_blue_green = np.float32(LUT_blue * maxCB * cG)
    
	hist = cv2.calcHist([source], [0], np.uint8(cG), [2**16], [0,2**16])
	maxCG = np.argmax(hist)
    
	LUT_green_red = np.float32(LUT_green * maxCG * cR)
	LUT_green_blue = np.float32(LUT_green * maxCG * cB)
	print(np.sum(source*cG))
	print(np.sum(LUT_blue_green))
	print(np.sum(LUT_red_green))    
	source = source - (LUT_red_blue + LUT_red_green + LUT_blue_red + LUT_blue_green + LUT_green_red + LUT_green_blue)
    
	hist = cv2.calcHist([source], [0], np.uint8(cR), [2**16], [0,2**16])
	maxCR = np.argmax(hist)

	hist = cv2.calcHist([source], [0], np.uint8(cG), [2**16], [0,2**16])
	maxCG = np.argmax(hist)
    
	hist = cv2.calcHist([source], [0], np.uint8(cB), [2**16], [0,2**16])
	maxCB = np.argmax(hist)
    
	ch1 = source * cR / maxCR / (LUT_red + np.ones(LUT_green.shape) * (cG + cB) )

	ch2 = source * cG / maxCG / (LUT_green + np.ones(LUT_green.shape) * (cR + cB) )
    
	ch3 = source * cB / maxCB/ (LUT_blue + np.ones(LUT_green.shape) * (cR + cG) )
    
	source = ch1 + ch2 + ch3
	return source

def __NormalizeImagesV2(source, LUT):

	[cR,cG,cB] = __createRGBMask(source.shape[0],source.shape[1])
	hist = cv2.calcHist([source], [0], np.uint8(cR), [2**16], [0,2**16])
	maxCR = np.argmax(hist)
	hist = cv2.calcHist([source], [0], np.uint8(cB), [2**16], [0,2**16])
	maxCB = np.argmax(hist)

	chR = source * cR / maxCR / (LUT+np.finfo(np.float32).eps)
	chB = source * cB / maxCB / (LUT+np.finfo(np.float32).eps)
	source = ( chR + chB )
	return source
	
def __NormalizeImagesGB(source, LUT_green, LUT_blue):
    [cR,cG,cB] = __createRGBMask(source.shape[0],source.shape[1])
    
    green_ChB = np.squeeze(LUT_green[:,:,0])
    green_readB = np.sum(green_ChB)/(green_ChB.shape[0] * green_ChB.shape[1])
    
    blue_ChG = np.squeeze(LUT_blue[:,:,1])
    blue_readG = np.sum(blue_ChG)/(blue_ChG.shape[0] * blue_ChG.shape[1])
    
    source = cv2.cvtColor(source, cv2.COLOR_BAYER_BG2BGR)
    
    realBlue = np.uint16(np.round(np.squeeze(source[:,:,0] - green_readB *source[:,:,1]) / (1 - green_readB * blue_readG)))
    realGreen = np.uint16(np.round(np.squeeze( - blue_readG * source[:,:,0] + source[:,:,1] ) / (1 - green_readB * blue_readG)))

    histB = cv2.calcHist([realBlue], [0], None, [2**16], [0,2**16-1])
    histG = cv2.calcHist([realGreen], [0], None, [2**16], [0,2**16-1])
    
    peakB = np.argsort(histB,axis=0)
    peakG = np.argsort(histG,axis=0)
    
    if peakB[-1]==65504:
        maxB = peakB[-2]
    else:
        maxB = peakB[-1]

    if peakG[-1]==65504:
        maxG = peakG[-2]
    else:
        maxG = peakG[-1]              
    
    norBlue = realBlue.astype(np.float32) / maxB / np.squeeze(LUT_blue[:,:,0])
    norGreen = realGreen.astype(np.float32) / maxG / np.squeeze(LUT_green[:,:,1])
    return np.array([norBlue, norGreen])    
	
def __cam_node_cmd(cam, cam_attr_str, cam_method_str, pyspin_mode_str=None, cam_method_arg=None):
    # Performs cam_method on input cam with optional access mode check
    # First, get camera attribute
    cam_attr = cam
    cam_attr_str_split = cam_attr_str.split('.')
    for sub_cam_attr_str in cam_attr_str_split:
        cam_attr = getattr(cam_attr, sub_cam_attr_str)

    # Print command info
    info_str = 'Executing: "' + '.'.join([cam_attr_str, cam_method_str]) + '('
    if cam_method_arg is not None:
        info_str += str(cam_method_arg)
    print(info_str + ')"')

    # Perform optional access mode check
    if pyspin_mode_str is not None:
        if cam_attr.GetAccessMode() != getattr(PySpin, pyspin_mode_str):
            raise RuntimeError('Access mode check failed for: "' + cam_attr_str + '" with mode: "' +
                               pyspin_mode_str + '".')

    # Format command argument in case it's a string containing a PySpin attribute
    if isinstance(cam_method_arg, str):
        cam_method_arg_split = cam_method_arg.split('.')
        if cam_method_arg_split[0] == 'PySpin':
            if len(cam_method_arg_split) == 2:
                cam_method_arg = getattr(PySpin, cam_method_arg_split[1])
            else:
                raise RuntimeError('Arguments containing nested PySpin arguments are currently not '
                                   'supported...')

    # Perform command
    if cam_method_arg is None:  # pylint: disable=no-else-return
        return getattr(cam_attr, cam_method_str)()
    else:
        return getattr(cam_attr, cam_method_str)(cam_method_arg)


def __cleanup_cam():
    # cleans up camera
    global __CAM

    # End acquisition and de-init
    with suppress(Exception):
        end_acquisition()
    with suppress(Exception):
        deinit()

    # Clear camera reference
    __CAM = None


def __find_cam(cam_serial):
    # returns camera object

    # Retrieve cameras from the system
    cam_list = __SYSTEM.GetCameras()

    # Find camera matching serial
    cam_found = None

    for i, cam in enumerate(cam_list):
        cam_found = cam
    # Check to see if match was found
    if cam_found is None:
        print('Could not find camera with serial: "' + str(cam_serial) + '".')
        return False

    return cam_found


def __get_image(cam):
    # Gets image and info from camera

    # Get image object
    image = cam.GetNextImage()

    # Initialize image dict
    image_dict = {}

    # Ensure image is complete
    if not image.IsIncomplete():
        # Get data/metadata
        image_dict['data'] = image.GetNDArray()
        image_dict['timestamp'] = image.GetTimeStamp()
        image_dict['bitsperpixel'] = image.GetBitsPerPixel()
    image.Release()
    return image_dict


# def __get_image_and_avg(cam, num_to_avg):
    # # Gets images and info from camera
    # try:
        # for i in range(0, num_to_avg):
            # # Get image object
            # image = cam.GetNextImage()

            # # Initialize image dict
            # image_dict = {}

            # # Ensure image is complete
            # if not image.IsIncomplete():
                # # Get data/metadata
                # if i == 0:
                    # img_array = np.array(image.GetNDArray(), dtype=np.float32)
                    # arr = img_array / num_to_avg
                    # #print('Frame: ' + str(datetime.now()))
                # else:
                    # img_array = np.array(image.GetNDArray(), dtype=np.float32) + img_array
                    # arr = arr + img_array / num_to_avg
                    # #print('Frame: ' + str(datetime.now()))
            # image.Release()
        # image_dict['data'] = arr
        # image_dict['timestamp'] = image.GetTimeStamp()
        # #print('Averaged Frame: ' + str(datetime.now()))
        # image_dict['bitsperpixel'] = image.GetBitsPerPixel()
    # except PySpin.SpinnakerException as ex:
        # print('Error: %s' % ex)
        # return False

    # return image_dict
    
def __get_image_and_avg(cam, num_to_avg):
    # Gets images and info from camera
    global __CAM
    nodemap = __CAM.GetNodeMap()
    node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
    node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
    image_size = [node_height.GetValue(), node_width.GetValue()]
    # Initialize image dict
    image_dict = {}
    arr = np.zeros((image_size[0], image_size[1]), dtype=np.float32)
    image_dict['image_size'] = image_size
    #print('EEExperiment start : ' + str(datetime.now()))
    try:
            
        for ii in range(0, num_to_avg):
            # Get image object
            image = cam.GetNextImage()
            #time.sleep(0.5)
            while image.IsIncomplete():
                print('INCOMPLETE')
                image = cam.GetNextImage()
            # Ensure image is complete
            if not image.IsIncomplete():
                # Get data/metadata                               
                arr = arr + np.array(image.GetNDArray(),dtype=np.float32) / num_to_avg
                #print('Frame: ' + str(datetime.now()))
                
            image.Release()
            
        #print('Experiment finish : ' + str(datetime.now()))     
        image_dict['data'] = arr
        image_dict['timestamp'] = image.GetTimeStamp() 
        
        image_dict['bitsperpixel'] = image.GetBitsPerPixel()
        
    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return image_dict    

def __get_image_and_return_array(cam, num_frames):
    # Gets images and info from camera
    global __CAM
    nodemap = __CAM.GetNodeMap()
    node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
    node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
    image_size = [node_height.GetValue(), node_width.GetValue()]
    # Initialize image dict
    image_dict = {}
    arr = np.zeros((image_size[0], image_size[1]), dtype=np.float32)
    image_dict['image_size'] = image_size
    print('EEExperiment start : ' + str(datetime.now()))
    try:
            
        for ii in range(0, num_frames):
            # Get image object
            #t1=time.time()
            image = cam.GetNextImage()
            #t2=time.time()
            #print("Getting camera Image took: "+ str((t2-t1)*1000))#time.sleep(0.5)
            while image.IsIncomplete():
                print('INCOMPLETE')
                image = cam.GetNextImage()
            # Ensure image is complete
            if not image.IsIncomplete():
                # Get data/metadata                               
                arr = arr + np.array(image.GetNDArray(),dtype=np.float32) / num_frames
                #print('Frame: ' + str(datetime.now()))
            image.Release()
            
        print('Experiment finish : ' + str(datetime.now()))     
        image_dict['data'] = arr
        image_dict['timestamp'] = image.GetTimeStamp() 
        
        image_dict['bitsperpixel'] = image.GetBitsPerPixel()
        
    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return image_dict   

def __get_image_and_return_polSig(cam, num_frames, LUT):
    # Gets images and info from camera
	global __CAM
	nodemap = __CAM.GetNodeMap()
	node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
	node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
	image_size = [node_height.GetValue(), node_width.GetValue()]
    # Initialize image dict
	image_dict = {}
	arr = np.zeros((num_frames, image_size[0], image_size[1]), dtype=np.float32)
	arr_im = np.zeros((num_frames, image_size[0], image_size[1]), dtype=np.float32)
	image_dict['image_size'] = image_size
	print('EEExperiment start : ' + str(datetime.now()))
	kernel1 = np.array( ( (1, 0), (0, -1) ), dtype = np.float32)
	kernel2 = np.array( ( (0, 1), (-1, 0) ), dtype = np.float32)
	try:
		    
		for ii in range(0, num_frames):
			# Get image object
			image = cam.GetNextImage()
            #time.sleep(0.5)
			while image.IsIncomplete():
				print('INCOMPLETE')
				image = cam.GetNextImage()
            # Ensure image is complete
			if not image.IsIncomplete():
                # Get data/metadata
				temp = np.array(image.GetNDArray(),dtype=np.float32)
				[height, width] = temp.shape
				[c0,c45,c90,c135] = __createPolMask(height, width)

				hist = cv2.calcHist([temp], [0], np.uint8(c0), [2**16], [0,2**16])
				maxC0 = np.argmax(hist)
				hist = cv2.calcHist([temp], [0], np.uint8(c90), [2**16], [0,2**16])
				maxC90 = np.argmax(hist)
				hist = cv2.calcHist([temp], [0], np.uint8(c45), [2**16], [0,2**16])
				maxC45 = np.argmax(hist)
				hist = cv2.calcHist([temp], [0], np.uint8(c135), [2**16], [0,2**16])
				maxC135 = np.argmax(hist)

				ch1 = temp * c0 / maxC0 / LUT
				ch2 = temp * c45 / maxC45 / LUT 
				ch3 = temp * c90 / maxC90 / LUT
				ch4 = temp * c135 / maxC135 / LUT 

				temp = ( ch1 + ch2 + ch3 + ch4 )  
                
				delta1 = cv2.filter2D(temp, -1, kernel1, anchor = (0,0), borderType = cv2.BORDER_ISOLATED)
				delta2 = cv2.filter2D(temp, -1, kernel2, anchor = (0,0), borderType = cv2.BORDER_ISOLATED)
				signal = delta1**2+delta2**2
				signal[0::,-1] = 0
				signal[-1,0::] = 0
				arr[ii,:,:] = np.array(signal)
				arr_im[ii,:,:] = np.array(temp)
                #print('Frame: ' + str(datetime.now()))
                
			image.Release()
            
		print('Experiment finish : ' + str(datetime.now()))     
		image_dict['data'] = np.mean(arr, axis=0)
		image_dict['image'] = np.mean(arr_im, axis=0)
		image_dict['timestamp'] = image.GetTimeStamp() 
        
		image_dict['bitsperpixel'] = image.GetBitsPerPixel()
        
	except PySpin.SpinnakerException as ex:
		print('Error: %s' % ex)
		return False

	return image_dict 

def __get_image_and_return_roProcess_v2(cam, num_frames, LUT):
    # Gets images and info from camera
	global __CAM
	nodemap = __CAM.GetNodeMap()
	node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
	node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
	image_size = [node_height.GetValue(), node_width.GetValue()]
	# Initialize image dict
	image_dict = {}
	arr = np.zeros((num_frames, image_size[0], image_size[1]), dtype=np.float32)
	image_dict['image_size'] = image_size
    # print('EEExperiment start : ' + str(datetime.now()))
	try:
		#t1 = time.time()    
		for ii in range(0, num_frames):

            # Get image object
			image = cam.GetNextImage()

            #time.sleep(0.5)
			while image.IsIncomplete():
				print('INCOMPLETE')
				image = cam.GetNextImage()
            # Ensure image is complete
			if not image.IsIncomplete():
				# Get data/metadata
				arr[ii,:,:] = np.array(image.GetNDArray(),dtype=np.float32)
                #print('Frame: ' + str(datetime.now()))
                
			image.Release()
		#t2 = time.time()
		#aqTime = t2-t1
        # print('Actual time: ' + str(t2-t1))
		#t1 = time.time()
		im = np.mean(arr, axis = 0)
		GB_stack = __NormalizeImagesV2(np.uint16(np.round(im)), LUT)
		[cR,cG,cB] = __createRGBMask(GB_stack.shape[0], GB_stack.shape[1])
		signal = (GB_stack[0:-1,0:-1] - GB_stack[1::,1::])**2 * (1-cG[0:-1,0:-1]) + (GB_stack[1::,0:-1] - GB_stack[0:-1,1::])**2 * (1-cG[1::,0:-1])
		#t2 = time.time()
		#proTime = t2-t1
		#delta1 = cv2.filter2D(im, -1, kernel1)
		#delta2 = cv2.filter2D(im, -1, kernel2)
		#signal = delta1**2+delta2**2
        # print('Experiment finish : ' + str(datetime.now()))     
		image_dict['data'] = signal
		image_dict['image'] = GB_stack
		image_dict['timestamp'] = image.GetTimeStamp() 
		#image_dict['aqTime'] = aqTime
		#image_dict['proTime'] = proTime
		image_dict['bitsperpixel'] = image.GetBitsPerPixel()
        
	except PySpin.SpinnakerException as ex:
		print('Error: %s' % ex)
		return False

	return image_dict 

def __get_polarization_images(cam, num_to_avg):
    # Gets images and info from camera
    global __CAM
    nodemap = __CAM.GetNodeMap()
    node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
    node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
    image_size = [node_height.GetValue(), node_width.GetValue()]
    # Initialize image dict
    arr = np.zeros((image_size[0]-1, image_size[1]-1), dtype=np.float32)
    image_dict = {}
    image_dict['image_size'] = image_size
    print('EEExperiment start : ' + str(datetime.now()))
    try:
        for ii in range(0, num_to_avg):
            # Get image object
            image = cam.GetNextImage()
            #time.sleep(0.5)
            while image.IsIncomplete():
                print('INCOMPLETE')
                image = cam.GetNextImage()
            # Ensure image is complete
            if not image.IsIncomplete():
                # Get data/metadata                               
                tempIm = np.array(image.GetNDArray(),dtype=np.float32) 
                [tempIm_x, tempIm_y] = np.shape(tempIm)
                kernel1 = np.array( ( (1, 0), (0, -1) ), dtype = np.float32)
                kernel2 = np.array( ( (0, 1), (-1, 0) ), dtype = np.float32)
                kernel3 = np.array( ( (0, 1), (-1, 0) ), dtype = np.float32)
                kernel4 = np.array( ( (1, 0), (0, -1) ), dtype = np.float32)
                delta1 = np.zeros( (tempIm_x-1, tempIm_y-1), np.float32)
                delta2 = np.zeros( (tempIm_x-1, tempIm_y-1), np.float32)
                
                delta1 = convolution(delta1, 1, tempIm, kernel1)
                delta1 = convolution(delta1, 2, tempIm, kernel3)
                
                delta2 = convolution(delta2, 1, tempIm, kernel2)
                delta2 = convolution(delta2, 1, tempIm, kernel4)
                
                signal = delta1**2+delta2**2
                arr = arr + signal / num_to_avg
                #print('Frame: ' + str(datetime.now()))
                
            image.Release()
            
            
        print('Experiment finish : ' + str(datetime.now()))     
        image_dict['data'] = arr
        image_dict['timestamp'] = image.GetTimeStamp() 
        
        image_dict['bitsperpixel'] = image.GetBitsPerPixel()
        
    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return image_dict    

def convolution(result, where, inputArr, kernel):
    [input_x, input_y] = np.shape(inputArr)
    [kernel_x, kernel_y] = np.shape(kernel)
    stride = 2
    iteration_x = ( input_x - kernel_x) / stride + 1
    iteration_y = ( input_y - kernel_y) / stride + 1
    if where == 1:
        for ii in range(iteration_x):
            for jj in range(iteration_y):
               result[2*ii, 2*jj] = np.sum( inputArr[ii*kernel_x:(ii+1)*kernel_x, jj*kernel_y:(jj+1)*kernel_y] * kernel )
    else:
        for ii in range(iteration_x):
            for jj in range(iteration_y):
               result[2*ii + 1, 2*jj + 1] = np.sum( inputArr[ii*kernel_x + 1:(ii+1)*kernel_x + 1
                                                     , jj*kernel_y + 1:(jj+1)*kernel_y + 1] * kernel ) 
    return result

def __init_cam(cam):
    # Init() camera
    cam.Init()


def __validate_cam(cam, cam_str):
    # Checks to see if camera is valid

    if not cam.IsValid():
        raise RuntimeError('Camera is not valid.')


def __validate_cam_init(cam, cam_str):
    # Checks to see if camera is valid and initialized

    __validate_cam(cam, cam_str)

    if not cam.IsInitialized():
        raise RuntimeError('Camera is not initialized.')


def __validate_cam_streaming(cam, cam_str):
    # Checks to see if camera is valid, initialized, and streaming

    __validate_cam_init(cam, cam_str)

    if not cam.IsStreaming():
        raise RuntimeError(cam_str + ' cam is not streaming. Please start_acquisition() it.')


def __roi():
    return 0


def set_video_mode(mode):
    global __CAM

    nodemap = __CAM.GetNodeMap()
    node_video_mode = PySpin.CEnumerationPtr(nodemap.GetNode("VideoMode"))
    if not PySpin.IsAvailable(node_video_mode) or not PySpin.IsWritable(node_video_mode):
        print('Unable to set VideoMode. Aborting...')
        return False

    node_video_mode_7 = node_video_mode.GetEntryByName("Mode7")
    if not PySpin.IsAvailable(node_video_mode_7) or not PySpin.IsReadable(node_video_mode_7):
        print('Unable to set VideoMode to Mode7 (entry retrieval). Aborting...')
        return False

    video_mode_7 = node_video_mode_7.GetValue()
    node_video_mode.SetIntValue(video_mode_7)
    print('Video Mode set to Mode ' + mode)


def __get_and_validate_init_cam():
    # Validates initialization and returns it

    cam = __get_cam()
    __validate_cam_init(cam, 'Camera')
    return cam


def __get_and_validate_streaming_cam():
    # Validates streaming of camera then returns it

    cam = __get_cam()
    __validate_cam_streaming(cam, 'Camera')
    return cam


def __get_cam():
    # Returns Camera

    if __CAM is None:
        raise RuntimeError('Camera not found')

    return __CAM


### Public Functions ###

def cam_node_cmd(cam_attr_str, cam_method_str, pyspin_mode_str=None, cam_method_arg=None):
    return __cam_node_cmd(__get_and_validate_init_cam(),
                          cam_attr_str,
                          cam_method_str,
                          pyspin_mode_str,
                          cam_method_arg)


def get_image():
    # Gets image from camera 
    return __get_image(__get_and_validate_streaming_cam())


def get_image_and_avg(num_to_avg):
    # Gets and averages images from camera 
    return __get_image_and_avg(__get_and_validate_streaming_cam(), num_to_avg)

def get_image_and_return_array(num_to_avg):
	# Gets and averages images from camera 
	return __get_image_and_return_array(__get_and_validate_streaming_cam(), num_to_avg)
    
def get_image_and_return_polSig(num_to_avg, LUT):
	# Gets and averages images from camera 
	return __get_image_and_return_polSig(__get_and_validate_streaming_cam(), num_to_avg, LUT)
    
def get_image_and_return_roProcess_v2(num_to_avg, LUT):
	# Gets and averages images from camera 
	return __get_image_and_return_roProcess_v2(__get_and_validate_streaming_cam(), num_to_avg, LUT)
    
def end_acquisition():
    # Ends acquisition
    __get_and_validate_streaming_cam().EndAcquisition()


def find_cam(cam_serial):
    # Finds Camera
    global __CAM

    cam = __find_cam(cam_serial)

    # Cleanup AFTER new camera is found successfully
    __cleanup_cam()

    # Assign camera
    __CAM = cam

    print('Found camera')


def set_gain(gain):
    cam_node_cmd('Gain',
                 'SetValue',
                 'RW',
                 gain)


def set_exposure(exposure):
    global __CAM
    
    if __CAM is None:
        raise RuntimeError('Camera not found')
    exposure_time_node = __CAM.ExposureTime
    if PySpin.IsWritable(exposure_time_node):
        print("Setting Exposure to {:.3f} microseconds".format(exposure))
        exposure_time_node.SetValue(exposure)
    else:
        print("Unable to write to the exposure time node")
        return False

def enable_frame_rate_control():
    global __CAM
    node_acquisition_frame_rate_enabled = __CAM.AcquisitionFrameRateEnable
    if PySpin.IsWritable(node_acquisition_frame_rate_enabled):
        node_acquisition_frame_rate_enabled.SetValue(True)
        print("Frame rate control enabled")
    else:
        print("Unable to enable frame rate control")

        
def set_frame_rate(frame_rate):
    global __CAM
    
    if __CAM is None:
        raise RuntimeError('Camera not found')
    frame_rate_node = __CAM.AcquisitionFrameRate
    if PySpin.IsWritable(frame_rate_node):
        print("Setting Frame Rate to {:.3f}".format(frame_rate))
        frame_rate_node.SetValue(frame_rate)
    else:
        print("Unable to write to the frame rate node")
        return False


def disable_auto_exp():
    print('Disabling Auto Exposure')
    cam_node_cmd('ExposureAuto',
                 'SetValue',
                 'RW',
                 PySpin.ExposureAuto_Off)


def disable_auto_gain():
    print('Disabling Auto Gain')
    cam_node_cmd('GainAuto',
                 'SetValue',
                 'RW',
                 PySpin.GainAuto_Off)


def disable_auto_frame():
    global __CAM
    nodemap = __CAM.GetNodeMap()

    node_acquisition_en = PySpin.CBooleanPtr(nodemap.GetNode('AcquisitionFrameRateEnabled'))
    if not PySpin.IsAvailable(node_acquisition_en) or not PySpin.IsWritable(node_acquisition_en):
        print('Unable to set enable acquisition frame rate. Aborting...')
        return False
    node_acquisition_en.SetValue(True)
    print('Enabling frame rate control')

    node_acquisition_auto = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionFrameRateAuto'))
    if not PySpin.IsAvailable(node_acquisition_auto) or not PySpin.IsWritable(
            node_acquisition_auto):
        print('Unable to turn off Auto Frame Rate. Aborting...')
        return False
    node_acquisition_auto_off = node_acquisition_auto.GetEntryByName('Off')
    if not PySpin.IsAvailable(node_acquisition_auto_off) or not PySpin.IsReadable(
            node_acquisition_auto_off):
        print('Unable to turn off Auto Frame Rate. Aborting...')
        return False
    node_acquisition_auto.SetIntValue(node_acquisition_auto_off.GetValue())


def set_gamma(gamma_val):
    print('Setting Gamma to ' + str(gamma_val))
    cam_node_cmd('Gamma',
                 'SetValue',
                 'RW',
                 gamma_val)


def get_exp_min():
    return cam_node_cmd('ExposureTime', 'GetMin')

def get_exp():
    global __CAM
    
    if __CAM is None:
        raise RuntimeError('Camera not found')
    exposure_time_node = __CAM.ExposureTime
    exposure_time_value = exposure_time_node.GetValue()
    return exposure_time_value
    

def get_exp_max():
    return cam_node_cmd('ExposureTime', 'GetMax')


def get_fps_min():
    return cam_node_cmd('AcquisitionFrameRate', 'GetMin')


def get_fps_max():
    return cam_node_cmd('AcquisitionFrameRate', 'GetMax')


def get_frame_rate():
    global __CAM
    
    if __CAM is None:
        raise RuntimeError('Camera not found')
    frame_rate_node = __CAM.AcquisitionFrameRate
    frame_rate_value = frame_rate_node.GetValue()
    return frame_rate_value


def init_cam():
    # Initializes camera
    __init_cam(__get_cam())


def start_acquisition():
    # Starts acquisition
    __get_and_validate_init_cam().BeginAcquisition()


def roi():
    # Select Region of Interest
    return __roi()
