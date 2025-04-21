import os
import cv2
import json
import numpy as np
import openslide
from PIL import Image
from shapely.geometry import Polygon, box
import xml.etree.ElementTree as ET

def parse_asap_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    rectangles = []
    polygons = []

    for annotation in root.findall(".//Annotation"):
        try:
            label = annotation.attrib["Name"]
        except:
            label = annotation.attrib.get("PartOfGroup", "Unknown")
        anno_type = annotation.attrib.get("Type", "Polygon")
        coords_el = annotation.find('Coordinates')
        coords = [(float(c.attrib["X"]), float(c.attrib["Y"])) for c in coords_el.findall('Coordinate')]
        if anno_type == "Rectangle":
            x1,y1 = coords[0]
            x2,y2 = coords[1]
            x,y = min(x1,x2),min(y1,y2)
            w,h = abs(x2 - x1), abs(y2 - y1)

            rectangles.append({
                "label":label,
                "bbox":[x,y,w,h],
                "polygon" : box(x,y,x+w,y+h)
            })
        elif (anno_type=='Spline' or anno_type=='Polygon') and len(coords) >= 3:
            sp_rect = cv2.boundingRect(np.array(coords,dtype=np.uint64))
            poly = Polygon(coords)
            polygons.append({
                "label": label,
                "bbox":sp_rect,
                "polygon" : box(sp_rect[0],sp_rect[1],sp_rect[0]+sp_rect[2],sp_rect[1]+sp_rect[3])
            })
    return rectangles, polygons


def tile_and_generate_coco(wsi_path, rectangles, polygons, output_dir,
                           tile_size= 512, stride = 512,level=0):
    slide = openslide.OpenSlide(wsi_path)
    downsample = slide.level_downsamples[level]
    sam_name = os.path.basename(wsi_path).split('.')[0]
    images = []
    annotations = []
    categories_dict = {}
    category_id_count = 1
    image_id = 1
    ann_id = 1

    os.makedirs(output_dir, exist_ok=True)

    for rect in rectangles:
        x0,y0,w,h = rect['bbox']
        x1= int(x0 + w)
        y1= int(y0 + h)

        for y in range(int(y0), y1, stride):
            for x in range(int(x0), x1, stride):
                read_size = int(tile_size*downsample)
                patch = slide.read_region( (int(x),int(y)),level, (tile_size,tile_size)).convert('RGB')
                patch_name = f"{sam_name}_{image_id}_{x}_{y}.png"
                patch_path = os.path.join(output_dir, patch_name)
                patch.save(patch_path)

                images.append({
                    'id':image_id,
                    'file_name':patch_name,
                    'width':tile_size,
                    'height':tile_size
                })

                tile_box = box(x, y, x + read_size, y + read_size)
                
                for poly in polygons:
                    if poly['polygon'].intersects(tile_box):
                        inter_poly = poly['polygon'].intersection(tile_box)
                        if not inter_poly.is_empty and inter_poly.geom_type == "Polygon":
                            coords = list(inter_poly.exterior.coords)
                            rel_coords = [((px-x) / downsample, (py-y)/ downsample) for px,py in coords]
                            segmentation = [sum(rel_coords, ())]
                            xs,ys = zip(*rel_coords)
                            bbox = [min(xs), min(ys), max(xs)-min(xs), max(ys) - min(ys)]

                            label = poly['label']
                            if label not in categories_dict:
                                categories_dict[label] = category_id_count
                                category_id_count += 1

                            annotations.append({
                                'id' : ann_id,
                                'image_id' : image_id,
                                'category_id' : categories_dict[label],
                                'segmentation' : segmentation,
                                'bbox': bbox,
                                'area' : inter_poly.area/(downsample ** 2),
                                'iscrowd' : 0 
                            })
                            ann_id += 1
                image_id += 1

    categories = [
        {'id':cid, 'name':name,'supercategory':'none'}
        for name, cid, in categories_dict.itmes()
    ]

    return {
        'image':images,
        'annotations':annotations,
        'categories':categories
    }

def main(xml_path, wsi_path,output_dir,output_json_path, tile_size = 512, stride = 512, level = 0):
    rects,polys = parse_asap_xml(xml_path)
    coco = tile_and_generate_coco(wsi_path,rects,polys, output_dir,tile_size = tile_size,stride = stride,level = level)
    with open(output_json_path, 'w') as f:
        json.dump(coco,f,indent=2)




