import requests, threading, os
import multiprocessing
from PIL import Image

url = 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2012-07-09/250m/6/{}/{}.jpg'
path_tmp = 'residual'

#The images are ordered in a queue;
#taking the coordinate as the central data
def matrix_base(row, column):	
	for i in range(9):
		queue.put((row+(i//3)-1, column+(i%3)-1, i+1))
		
#Finding maximum limit in columns and rows, to avoid overloadFinding 
#maximum limit in columns and rows, to avoid overload
def limit_max(row, column):
	max_ = requests.get(url.format(row, column))
	max_ = int(max_.text.split('maximum value is', 1)[-1].split('<')[0].strip())
	limits.append(max_)
	
#Write the images on disk.
def write_img(file, name):
	if not os.path.exists(path_tmp):
		os.mkdir('residual')
	with open(f'{path_tmp}/{name}.jpg', 'wb') as f:
		f.write(file)

#Download the images, checking that they are within the limits, in order.
def download_set(queue, limits):
	while not queue.empty():
		row, col, id_name = queue.get(block=True)
		if (row<limits[0]) and (col<limits[1]):
			response = requests.get(url.format(row, col))
			if response:
				write_img(response.content, str(id_name))
	
#We joined the mosaic into a single navigation image.
def join_mosaic(name):
	width = 512
	height = 512
	
	img_aux= Image.new('RGB', (width*3, height*3), color=(0, 0, 0))

	for i in range(0, 9):
		img = Image.open(f'{path_tmp}/{i+1}.jpg')
		img_aux.paste(img, ((i%3)*width, (i//3)*height))
		print((i%3)*width, (i//3)*height)
			
	img_aux.save(f'{name}.jpg')

	
if __name__ == '__main__':
	
	#Maximum limits.
	limits = []

	#We generate a queue to manage the access to the memory of the processes.
	manager = multiprocessing.Manager()
	queue = manager.Queue()

	#We use threads to speed up the search for boundaries.
	thr_rows = threading.Thread(target=limit_max, args=('1000', '0')) #rows
	thr_column = threading.Thread(target=limit_max, args=('0', '1000')) #columns
	
	thr_rows.start()
	thr_column.start()	
	
	#While finding the maxima, we generate the base array of coordinates (row, column, id_name)
	matrix_base(15, 50)

	thr_rows.join()
	thr_column.join()
	
	#We ordered, knowing that no matter the zoom, the columns in this projection will always be larger than the total rows.
	limits.sort()
	
	#We downloaded the set of images using concurrence.
	pro1 = multiprocessing.Process(target=download_set, args=(queue, limits) )
	pro1.start()
	
	pro2 = multiprocessing.Process(target=download_set, args=(queue, limits))
	pro2.start()
	
	pro1.join()
	pro2.join()
	
	#We collect the downloaded images, and save them with a 'name'.
	join_mosaic('Total')
	
	

