from pycocotools.coco import COCO
import matplotlib.pyplot as plt
import cv2
import os

# 경로 설정

annotation_file = './annotation.json' # COCO 포멧 json 파일
image_dir = './patches' # 이미지 폴더


coco =COCO(annotation_file)

image_ids = coco.getImgIds()
img_info = coco.loadImgs(image_ids[0])[0] # image_dir에서 첫번째 이미지에다 annotation결과 확인

image_path = os.path.join(image_dir, img_info['file_name'])
image = cv2.imred(image_path)
image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

# annotation 불러오기
ann_ids = coco.getAnnIds(imgIds=img_info['id'])
annotations = coco.loadAnns(ann_ids)

plt.imshow(image)
ax = plt.gca()

for ann in annotaitons:
    bbox = ann['bbox']
    x,y,w,h = bbox
    ## 사각형으로 표시?
    # rect = plt.Rectangle((x,y,),w,h, fill=False, edgecolor = 'red',linewidth = 2)
    # ax.add_patch(rect)
    ##
    ## 점으로 표시
    cx,cy = x + w/2, y + h/2
    ax.plot(cx,cy, 'bo')
    ##
    category = coco.loadCats(ann['category_id'])[0]['name']
    plt.text(x,y,category,color= 'white',backgroundcolor='red',fontsize = 8)
plt.axis('off')