import os
import json
from os.path import join, basename, dirname
import base64
import requests
from PIL import Image

LANGUAGES = {
	'hindi': 'hi',
	'english': 'en',
	'marathi': 'mr',
	'tamil': 'ta',
	'telugu': 'te',
	'kannada': 'kn',
	'gujarati': 'gu',
	'punjabi': 'pa',
	'bengali': 'bn',
	'malayalam': 'ml',
	'assamese': 'asa',
	'manipuri': 'mni',
	'oriya': 'ori',
	'urdu': 'ur',
}

#image_path = '/home/krishna/projects/pageocr/image.jpg'
image_path = '/home/rashid/Desktop/bhashini-transzaar-demo/pageocr/image.jpg'

def call_layout_parser(image_path: str, model: str = 'v2_doctr'):
	"""
	function to the call the layout parser API

	@returns the list of the regions of the word level parser
	"""
	url = "https://ilocr.iiit.ac.in/layout/"
	files=[
		(
			'images',
			(
				basename(image_path),		# filename
				open(image_path,'rb'),		# file object
				'image/jpeg'				# file mimetype
			)
		)
	]
	response = requests.post(
		url,
		headers={},
		data={
			'model': model
		},
		files=files
	)
	return response.json()[0]['regions']

def crop_regions(image_path: str, regions) -> str:
	"""
	crop the original image given the regions output of the layout parser
	and saves each of the word in a separate image inside folder

	@returns the path where cropped images are saved
	"""
	# folder to save all the word level cropped images
	ret = join(
		dirname(image_path),
		basename(image_path).strip().split('.')[0],
	)
	os.makedirs(ret)
	img = Image.open(image_path)
	bboxes = [i['bounding_box'] for i in regions]
	bboxes = [(i['x'], i['y'], i['x']+i['w'], i['y']+i['h']) for i in bboxes]
	for idx, bbox in enumerate(bboxes):
		with open(join(ret, '{}.jpg'.format(idx)), 'wb+') as f:
			img.crop(bbox).save(f)
	return ret

def perform_ocr(path: str, language: str, version: str, modality: str = 'printed'):
	"""
	call the ocr API on all the images inside the path folder

	Because when selecting the language from the index page. we call the
	the concerned ocr model is loaded into the beforehand, so we specify
	the preloaded=true by default in the ocr api url
	"""
	a = os.listdir(path)
	a = sorted(a, key=lambda x:int(x.strip().split('.')[0]))
	a = [join(path, i) for i in a if i.endswith('jpg')]
	a = [base64.b64encode(open(i, 'rb').read()).decode() for i in a]
	ocr_request = {
		'imageContent': a,
		'modality': modality,
		'language': LANGUAGES[language],
		'version': version,
	}
	url = "https://ilocr.iiit.ac.in/ocr/infer"
	response = requests.post(url, headers={
		'Content-Type': 'application/json'
	}, data=json.dumps(ocr_request))
	ret = response.json()
	ret = [i['text'] for i in ret]
	return ret

def format_ocr_output(ocr, regions) -> str:
	"""
	takes the word level ocr output for all the words and corresponding
	regions extracted from the layout-parser and constructs the
	proper output string.

	@returns the final page level ocr output with appropriate '\n'
	"""
	ret = []
	lines = [i['line'] for i in regions]
	assert len(lines) == len(ocr)
	prev_line = lines[0]
	tmp_line = []
	for line, text in zip(lines, ocr):
		if line == prev_line:
			tmp_line.append(text)
		else:
			prev_line = line
			ret.append(' '.join(tmp_line))
			tmp_line = [text]
	# this is so that the last line is also included in the ret
	ret.append(' '.join(tmp_line))
	ret = [i.strip() for i in ret]
	ret = '\n'.join(ret).strip()
	return {
		'text': ret,
		'regions': regions
	}
	# regions = [Region(**i) for i in regions]
	# return PageOCRResponse(
	# 	text=ret,
	# 	regions=regions
	# )

def main():
	regions = call_layout_parser(image_path, 'v2_doctr')
	print('completed layout parser')
	path = crop_regions(image_path, regions)
	print('completed cropping')
	ocr_output = perform_ocr(path, 'hindi', 'v4_robust', 'printed')
	print('completed ocr')
	return format_ocr_output(ocr_output, regions)

if __name__ == '__main__':
	out = main()
	with open('out.json', 'w', encoding='utf-8') as f:
		f.write(json.dumps(out, indent=4))
