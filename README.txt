Install tesseract ocr -->https://github.com/tesseract-ocr/tesseract --> click the green 'Code' button and download zip.

pip install - pytesseract, pillow, pdf2image, openpyxl
pytesseract is an api wrapper for this engine

Install poppler - for pdf2image -->https://github.com/oschwartz10612/poppler-windows/releases/download/v25.07.0-0/Release-25.07.0-0.zip

Set PATH env variable for tesseract folder
Set PATH to poppler/Library/bin (or) directly include that path in python code. the latter has been implemented in the project.

Download xampp from here --> https://sourceforge.net/projects/xampp/

Clone the git repo or copy files to your system. The project folder MUST be inside htdocs folder in the xampp folder.
Start apache in xampp and paste this link into browser tab -->http://localhost//pdf_to_excel/frontend/frontend.html

project structure:
pdf_to_excel:
	backend:
		pdf_to_excel.py
		upload.php
	frontend:
		front.txt
		frontend.html
	uploads - pdf will be stored here
	outputs - excel files will be stored here
	README.txt - info about the project