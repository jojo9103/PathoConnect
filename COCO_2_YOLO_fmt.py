import json
import os
def coco_to_yolo(json_path,output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(json_path,'r') as r:
        data = json.load(f)
    image_info = {img['id']: img for img in data['images']}

    yolo_labels = {}

    for ann in data['annotations']:
        img = image_info['image_id']
        img_w, img_h = img['width'],img['height']
        x,y,w,h = ann['bbox']

        xc  = (x+w/2) /img_w
        yc = (y+h/2) /img_h
        nw = w/img_w
        nh = h/img_h

        line = f"{ann['category_id']} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}"
        yolo_labels.setdefault(img['file_name'],[]).append(line)
        
    for filename, lines in yolo_labels.items():
        label_path = os.path.join(output_dir,filename.replace('.png','.txt'))
        with open(label_path,'w') as f:
            f.write('\n'.join(lines))
            
    print(f"YOLO labels saved to {output_dir}")