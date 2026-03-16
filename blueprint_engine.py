import cv2
import pytesseract
import fitz  # PyMuPDF
import numpy as np
import re
import tempfile
import os

class BlueprintEngine:
    def __init__(self):
        pass

    def pdf_to_image(self, uploaded_file):
        """
        Converts an uploaded Streamlit PDF file stream into OpenCV images.
        Uses a temporary file so PyMuPDF can read it from the OS.
        """
        images = []
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_file.read())
            temp_path = temp_pdf.name
            
        try:
            doc = fitz.open(temp_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n >= 4:
                    img_cv = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                else:
                    img_cv = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    
                images.append(img_cv)
            doc.close()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        return images
        
    def process_image(self, uploaded_file):
        """
        Processes a generic image upload directly into cv2 format.
        """
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img_cv = cv2.imdecode(file_bytes, 1)
        return [img_cv]

    def extract_dimensions(self, image):
        """
        OCR-based dimension extraction.
        Returns a list of components with width/height info.
        Example output:
        [
          {"component": "roof", "width": 24, "length": 36},
          {"component": "wall", "width": 10, "length": 24}
        ]
        """
        # Improved OCR precision
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        text = pytesseract.image_to_string(thresh)
        components = []

        # Simple regex parsing for "Roof 24'x36'" etc.
        pattern = r"([A-Za-z]+)\s+(\d+)'x(\d+)'"
        matches = re.findall(pattern, text)

        for match in matches:
            component, w, l = match
            components.append({
                "component": component.lower().strip(),
                "width": int(w),
                "length": int(l)
            })

        return components

    def calculate_materials(self, components, assemblies):
        """
        Convert extracted dimensions into material quantities.
        Uses the assemblies.csv logic mapping (e.g. arch_shingle_roof)
        """
        material_list = []

        for comp in components:
            if "roof" in comp["component"]:
                sq = (comp["width"] * comp["length"]) / 100  # 1 sq = 100 sq ft
                roof_assembly = assemblies[assemblies["assembly"] == "arch_shingle_roof"]
                
                for _, row in roof_assembly.iterrows():
                    material_list.append({
                        "module": comp["component"],
                        "material": row["material"],
                        "quantity": row["quantity"] * sq,
                        "unit": row["unit"]
                    })
                    
            # Extensible to walls, windows, floors, etc.
            if "wall" in comp["component"]:
                 # Just as an example placeholder for another module
                 sq_ft = comp["width"] * comp["length"]
                 material_list.append({
                     "module": comp["component"],
                     "material": "Generic Drywall",
                     "quantity": sq_ft,
                     "unit": "sqft"
                 })

        return material_list
