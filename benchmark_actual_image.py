# File to initialize 2D image, pass input image to kernel, and peform timing analyis on output image.
# Authors. Kaylo Littlejohn and Desmond Yao 2019.
#!/usr/bin/env python
import numpy as np
import time
import math
from dwt_serial import *
from dwt_naive_separable_parallel import *
from dwt_nonseparable_parallel import *
import numpy as np
import pywt
from dwt_tiled_separable_parallel import *
import os
import matplotlib.pyplot as plt
import os, os.path
import matplotlib.image as mpimg
import pywt.data
from PIL import Image

# Data set specifications (750 images total):
# Square .jpg images ranging from 100x100 to 1000x1000 in set of 25 per 100 pixel increments (250 total)
# Rect .jpg images  matricies ranging from 200x100 / 100x200 to 2000x1000 / 1000x2000 in set of 25 per 100 pixel increments (500 total)

#file path assuming images are stored in same directory as project
projdir = os.getcwd()

#create list to hold rgb_images
imgs = []

#Load every image into python
for i in range(30):
    
    #decide which type of image (square, rect wide, rect tall) to load and load image into RGB components
    if(i<10):
        #square
        #get directory dimension value
        dimdir = str(np.int32((i+1)*100))
        
        #load rgb matrix into list
        path = projdir+'/images/square/square'+dimdir+'/'
        valid_images = [".jpg"]
        for f in os.listdir(path):
            ext = os.path.splitext(f)[1]
            #ignore non-image files
            if ext.lower() not in valid_images:
                continue
            #append image list
            cur_img =mpimg.imread(os.path.join(path,f))
            imgs.append(cur_img)
        
    if 10 <= i and i < 20:
        #rect wide         
        #get directory dimension value
        dimdir = str(np.int32((i+1-10)*100))
                        
        #load rgb matrix into list
        path = projdir+'/images/rect_wide/rect'+dimdir+'/'
        valid_images = [".jpg"]
        for f in os.listdir(path):
            ext = os.path.splitext(f)[1]
            #ignore non-image files
            if ext.lower() not in valid_images:
                continue
            #append image list
            cur_img =mpimg.imread(os.path.join(path,f))
            imgs.append(cur_img)
        
    if i >= 20:
        #rect tall
        #get directory dimension value
        dimdir = str(np.int32((i+1-20)*100))
                        
        #load rgb matrix into list
        path = projdir+'/images/rect_tall/rect'+dimdir+'/'
        valid_images = [".jpg"]
        for f in os.listdir(path):
            ext = os.path.splitext(f)[1]
            #ignore non-image files
            if ext.lower() not in valid_images:
                continue
            #append image list
            cur_img =mpimg.imread(os.path.join(path,f))
            imgs.append(cur_img)

# Define the coefficients for the CDF9/7 filters
factor = 1

# Forward Decomposition filter: lowpass
cdf97_an_lo = factor * np.array([0, 0.026748757411, -0.016864118443, -0.078223266529, 0.266864118443,
                                 0.602949018236, 0.266864118443, -0.078223266529, -0.016864118443,
                                 0.026748757411])

# Forward Decomposition filter: highpass
cdf97_an_hi = factor * np.array([0, 0.091271763114, -0.057543526229, -0.591271763114, 1.11508705,
                                 -0.591271763114, -0.057543526229, 0.091271763114, 0, 0])

# Inverse Reconstruction filter: lowpass
cdf97_syn_lo = factor * np.array([0, -0.091271763114, -0.057543526229, 0.591271763114, 1.11508705,
                                  0.591271763114, -0.057543526229, -0.091271763114, 0, 0])

# Inverse Reconstruction filter: highpass
cdf97_syn_hi = factor * np.array([0, 0.026748757411, 0.016864118443, -0.078223266529, -0.266864118443,
                                  0.602949018236, -0.266864118443, -0.078223266529, 0.016864118443,
                                  0.026748757411])
filters = np.vstack((cdf97_an_lo, cdf97_an_hi, cdf97_syn_lo, cdf97_syn_hi)).astype(np.float32)

#define arrays to hold our execution times, size arrays, and temporary variables
times_serial_square = []
times_naive_square = []
sizes_square = []
times_opt_square = []
times_til_square = []
times_serial_rectw = []
times_naive_rectw = []
sizes_rectw = [] 
times_opt_rectw = []
times_til_rectw = []
times_serial_rectt = []
times_naive_rectt = []
sizes_rectt = [] 
times_opt_rectt = []
times_til_rectt = []
temp_s = 0
temp_naive = 0
temp_o = 0
temp_til = 0

#define the block width to be used (32 when working with full data set of 750 images, see code for random signal for
#analysis with varying block width
BLOCK_WIDTH = 32

#for each image in our grand list
for i in range(750):
    
    #decompose image into RGB
    # normalize every image by dividing by 255
    rgb_cpu = imgs[i].astype(np.float32)/255
    rsig = np.ascontiguousarray(rgb_cpu[:,:,0], dtype=np.float32)
    gsig = np.ascontiguousarray(rgb_cpu[:,:,1], dtype=np.float32)
    bsig = np.ascontiguousarray(rgb_cpu[:,:,2], dtype=np.float32)
    
    #get matrix size
    size = rgb_cpu.shape[0]*rgb_cpu.shape[1]
    
    """
    1. Test serial with r,g,b components of image.
    """
    #generate wavelet
    wav = gen_wavelet()
    
    #perform serial 2D DWT on r g b component matricies
    rcA, rcH, rcV, rcD, serial_time_r = run_DWT(rsig, wav, False, mode='zero')
    gcA, gcH, gcV, gcD, serial_time_g = run_DWT(gsig, wav, False, mode='zero')
    bcA, bcH, bcV, bcD, serial_time_b = run_DWT(bsig, wav, False, mode='zero')
    
    #concatenate serial execution times and average to get a final value for execution time across 2D dwts per matrix size
    serial_time = serial_time_r + serial_time_g + serial_time_b
    temp_s = temp_s + serial_time
    if(np.mod((i+1),25)==0):
        #append arrays holding serial times and size results (separate squares and rectangles)
        if(rsig.shape[0] == rsig.shape[1]):
            times_serial_square.append(temp_s/25)
            sizes_square.append(size/1000)
        elif (rsig.shape[0] > rsig.shape[1]):
            times_serial_rectw.append(temp_s/25)
            sizes_rectw.append(size/1000)
        else:
            times_serial_rectt.append(temp_s/25)
            sizes_rectt.append(size/1000)
        temp_s = 0

    """
    2. Test parallel with some random array

    """

    #implement naive separable version of 2D dwt
    dwt_naive = DWT_naive_separable()
    rh_cA, rh_cH, rh_cV, rh_cD, kernel_time_r = dwt_naive.dwt_gpu_naive_separable(rsig, filters, BLOCK_WIDTH)
    gh_cA, gh_cH, gh_cV, gh_cD, kernel_time_g = dwt_naive.dwt_gpu_naive_separable(gsig, filters, BLOCK_WIDTH)
    bh_cA, bh_cH, bh_cV, bh_cD, kernel_time_b = dwt_naive.dwt_gpu_naive_separable(bsig, filters, BLOCK_WIDTH)

    #implement nonseparable version of 2D dwt
    dwt_nonseparable = DWT_nonseparable()
    rh_cAo, rh_cHo, rh_cVo, rh_cDo, kernel_time_or = dwt_nonseparable.dwt_gpu_nonseparable(rsig, filters, BLOCK_WIDTH)
    gh_cAo, gh_cHo, gh_cVo, gh_cDo, kernel_time_og = dwt_nonseparable.dwt_gpu_nonseparable(gsig, filters, BLOCK_WIDTH)
    bh_cAo, bh_cHo, bh_cVo, bh_cDo, kernel_time_ob = dwt_nonseparable.dwt_gpu_nonseparable(bsig, filters, BLOCK_WIDTH)
    
    #implement optimized separable version of 2D dwt
    dwt_tiled = DWT_tiled_separable()
    rh_cAt, rh_cHt, rh_cVt, rh_cDt, kernel_time_tr = dwt_tiled.dwt_gpu_tiled_separable(rsig, filters, BLOCK_WIDTH)
    gh_cAt, gh_cHt, gh_cVt, gh_cDt, kernel_time_tg = dwt_tiled.dwt_gpu_tiled_separable(gsig, filters, BLOCK_WIDTH)
    bh_cAt, bh_cHt, bh_cVt, bh_cDt, kernel_time_tb = dwt_tiled.dwt_gpu_tiled_separable(bsig, filters, BLOCK_WIDTH)
    
    #concatenate kernel execution times and average to get a final value for execution time across 2D dwts per matrix size
    temp_naive = temp_naive + kernel_time_r + kernel_time_g + kernel_time_b
    temp_o = temp_o + kernel_time_or + kernel_time_og + kernel_time_ob
    temp_til = temp_til + kernel_time_tr + kernel_time_tg + kernel_time_tb
    if(np.mod((i+1),25)==0):
        #append arrays holding kernel times and size results (separate squares and rectangles)
        if(rsig.shape[0] == rsig.shape[1]):
            times_naive_square.append(temp_naive/25)
            times_opt_square.append(temp_o/25)
            times_til_square.append(temp_til/25)
        elif (rsig.shape[0] > rsig.shape[1]):
            times_naive_rectw.append(temp_naive/25)
            times_opt_rectw.append(temp_o/25)
            times_til_rectw.append(temp_til/25)
        else:
            times_naive_rectt.append(temp_naive/25)
            times_opt_rectt.append(temp_o/25)
            times_til_rectt.append(temp_til/25)
        temp_naive = 0
        temp_o = 0
        temp_til = 0

    #print outputs and timing results
    print('\nnaive same as serial rc_A: {}'.format(np.allclose(rcA, rh_cA, atol=5e-7)))
    print('naive same as serial rc_H: {}'.format(np.allclose(rcH, rh_cH, atol=5e-7)))
    print('naive same as serial rc_V: {}'.format(np.allclose(rcV, rh_cV, atol=5e-7)))
    print('naive same as serial rc_D: {}'.format(np.allclose(rcD, rh_cD, atol=5e-7)))
    print('naive same as serial gc_A: {}'.format(np.allclose(gcA, gh_cA, atol=5e-7)))
    print('naive same as serial gc_H: {}'.format(np.allclose(gcH, gh_cH, atol=5e-7)))
    print('naive same as serial gc_V: {}'.format(np.allclose(gcV, gh_cV, atol=5e-7)))
    print('naive same as serial gc_D: {}'.format(np.allclose(gcD, gh_cD, atol=5e-7)))
    print('naive same as serial bc_A: {}'.format(np.allclose(bcA, bh_cA, atol=5e-7)))
    print('naive same as serial bc_H: {}'.format(np.allclose(bcH, bh_cH, atol=5e-7)))
    print('naive same as serial bc_V: {}'.format(np.allclose(bcV, bh_cV, atol=5e-7)))
    print('naive same as serial bc_D: {}'.format(np.allclose(bcD, bh_cD, atol=5e-7)))
    
    print('nonseparable same as serial rc_A: {}'.format(np.allclose(rcA, rh_cAo, atol=5e-7)))
    print('nonseparable same as serial rc_H: {}'.format(np.allclose(rcH, rh_cHo, atol=5e-7)))
    print('nonseparable same as serial rc_V: {}'.format(np.allclose(rcV, rh_cVo, atol=5e-7)))
    print('nonseparable same as serial rc_D: {}'.format(np.allclose(rcD, rh_cDo, atol=5e-7)))
    print('nonseparable same as serial gc_A: {}'.format(np.allclose(gcA, gh_cAo, atol=5e-7)))
    print('nonseparable same as serial gc_H: {}'.format(np.allclose(gcH, gh_cHo, atol=5e-7)))
    print('nonseparable same as serial gc_V: {}'.format(np.allclose(gcV, gh_cVo, atol=5e-7)))
    print('nonseparable same as serial gc_D: {}'.format(np.allclose(gcD, gh_cDo, atol=5e-7)))
    print('nonseparable same as serial bc_A: {}'.format(np.allclose(bcA, bh_cAo, atol=5e-7)))
    print('nonseparable same as serial bc_H: {}'.format(np.allclose(bcH, bh_cHo, atol=5e-7)))
    print('nonseparable same as serial bc_V: {}'.format(np.allclose(bcV, bh_cVo, atol=5e-7)))
    print('nonseparable same as serial bc_D: {}'.format(np.allclose(bcD, bh_cDo, atol=5e-7)))

    print('tiled same as serial rc_A: {}'.format(np.allclose(rcA, rh_cAt, atol=5e-7)))
    print('tiled same as serial rc_H: {}'.format(np.allclose(rcH, rh_cHt, atol=5e-7)))
    print('tiled same as serial rc_V: {}'.format(np.allclose(rcV, rh_cVt, atol=5e-7)))
    print('tiled same as serial rc_D: {}'.format(np.allclose(rcD, rh_cDt, atol=5e-7)))
    print('tiled same as serial gc_A: {}'.format(np.allclose(gcA, gh_cAt, atol=5e-7)))
    print('tiled same as serial gc_H: {}'.format(np.allclose(gcH, gh_cHt, atol=5e-7)))
    print('tiled same as serial gc_V: {}'.format(np.allclose(gcV, gh_cVt, atol=5e-7)))
    print('tiled same as serial gc_D: {}'.format(np.allclose(gcD, gh_cDt, atol=5e-7)))
    print('tiled same as serial bc_A: {}'.format(np.allclose(bcA, bh_cAt, atol=5e-7)))
    print('tiled same as serial bc_H: {}'.format(np.allclose(bcH, bh_cHt, atol=5e-7)))
    print('tiled same as serial bc_V: {}'.format(np.allclose(bcV, bh_cVt, atol=5e-7)))
    print('tiled same as serial bc_D: {}'.format(np.allclose(bcD, bh_cDt, atol=5e-7)))
    
    print('Serial time: {}'.format(serial_time))
    print('Naive time: {}'.format(kernel_time_r + kernel_time_g + kernel_time_b))
    print('nonseparable time: {}'.format(kernel_time_or + kernel_time_og + kernel_time_ob))
    print('Tiled time: {}'.format(kernel_time_tr + kernel_time_tg + kernel_time_tb))
    
    #output images to display
    if i == 99:
        
        #run the pywt inverse DWT
        cA_empty = np.zeros(rcA.shape)
        cH_empty = np.zeros(rcH.shape)
        cV_empty = np.zeros(rcV.shape)
        cD_empty = np.zeros(rcD.shape)
        approx_imgr = run_iDWT(wav, rcA, cH_empty, cV_empty, cD_empty, mode='zero')
        approx_imgg = run_iDWT(wav, gcA, cH_empty, cV_empty, cD_empty, mode='zero')
        approx_imgb = run_iDWT(wav, bcA, cH_empty, cV_empty, cD_empty, mode='zero')
        
        #convert arrays to images and save
        approx_img = np.zeros((approx_imgr.shape[0],approx_imgr.shape[1],3),dtype=np.float32)
        approx_img[:,:,0] = approx_imgr
        approx_img[:,:,1] = approx_imgg
        approx_img[:,:,2] = approx_imgb
        plt.imsave("Results/approximation_image.png",approx_img)
        plt.imsave("Results/original_image.png",imgs[i])
    
#save timing results
plt.figure()
plt.title('Image 2D DWT Execution Time Comparison Graph (SQUARE)')
plt.plot(sizes_square, times_naive_square, label='Separable')
plt.plot(sizes_square, times_opt_square, label='Nonseparable')
plt.plot(sizes_square, times_serial_square, label='Serial')
plt.plot(sizes_square, times_til_square, label='Tiled')
plt.xlabel('Number of Pixels (10^3)')
plt.ylabel('run time/s')
plt.legend(loc='upper right')
plt.savefig('image_exc_time_square.png')

plt.figure()
plt.title('Image 2D DWT Execution Time Comparison Graph (RECT WIDE)')
plt.plot(sizes_rectw, times_naive_rectw, label='Separable')
plt.plot(sizes_rectw, times_opt_rectw, label='Nonseparable')
plt.plot(sizes_rectw, times_serial_rectw, label='Serial')
plt.plot(sizes_rectw, times_til_rectw, label='Tiled')
plt.xlabel('Number of Pixels (10^3)')
plt.ylabel('run time/s')
plt.legend(loc='upper right')
plt.savefig('image_exc_time_rect_wide.png')

plt.figure()
plt.title('Image 2D DWT Execution Time Comparison Graph (RECT_TALL)')
plt.plot(sizes_rectt, times_naive_rectt, label='Separable')
plt.plot(sizes_rectt, times_opt_rectt, label='Nonseparable')
plt.plot(sizes_rectt, times_serial_rectt, label='Serial')
plt.plot(sizes_rectt, times_til_rectt, label='Tiled')
plt.xlabel('Number of Pixels (10^3)')
plt.ylabel('run time/s')
plt.legend(loc='upper right')
plt.savefig('image_exc_time_rect_tall.png')
