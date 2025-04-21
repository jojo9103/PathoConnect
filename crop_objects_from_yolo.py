import os
import cv2
## 이미지에서 객체를 crop해서 해당 이미지이름의 폴더에 저장하는 기능
def crop_objects_from_yolo(image_dir,label_dir,output_dir):
    os.makedirs(output_dir,exist_ok=True)

    for label_file in os.listdir(label_dir):
        if not label_file.endswith('.txt'):
            continue

        base_name = os.path.splitext(label_file)[0]
        image_name = base_name+'.png'
        image_path = os.path.join(image_dir,image_name)
        label_path = os.path.join(label_dir,label_file)

        if not os.path.exists(image_path):
            print(f"이미지 없음 : {image_path}")
            continue

        img = cv2.imread(image_path)
        img_h, img_w = img.shape[:2]

        img_output_dir = os.path.join(output_dir,base_name)
        os.makedirs(img_output_dir,exist_ok=True)

        with open(label_path,'r') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls_id, x,y,w,h = map(float, parts)

            x1 = int((x - w / 2) * img_w)
            y1 = int((y - h / 2) * img_h)
            x2 = int((x + w / 2) * img_w)
            y2 = int((y + h / 2) * img_h)

            x1, y1 = max(0,x1), max(0,y1)
            x2, y2 = min(img_w,x2), min(img_h, y2)

            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            crop_path = os.path.join(img_output_dir, f'obj{idx}.jpg')
            cv2.imwrite(crop_path,crop)

    print("Crop 완료, 각 이미지 별로 폴더 저장됨.")