## 아직 안해봄.

import json
import xml.etree.ElementTree as ET
import os, glob, argparse, math

def hex_to_rgb(hex_color):
    """HEX색상 코드를 RGB 정수 값으로 변환"""
    hex_color= hex_color.lstrip('#')
    r = int(hex_color[0:2],16)
    g = int(hex_color[2:4],16)
    b = int(hex_color[4:6],16)

    return (r<<16) | (g<<8) | b
### hex -> rgb 변환되는 과정


def asap_xml_to_geojson(xml_path, output_geojson_path, scale_factor = 1.0 ,offset_x=0,offset_y=0):
    """ASAP XML을 QuPath GeoJSON으로 변환"""
    # XML 파일 로드
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # GeoJSON 구조 생성

    geojson = {
        "type" : "FeatureCollection",
        "features" : []
    }

    groups = {}

    for group_elem in root.findall('./AnnotationGroups/Group'):
        group_name = group_elem.get('Name')
        group_color = group_elem.get('Color','#F4FA58')
        groups[group_name]={
            'color': group_color,
            'colorRGB':hex_to_rgb(group_color)
        }

    for idx, annotation in enumerate(root.findall('./Annotations/Annotation')):
        annotation_type = annotation.get('Type')
        group_name = annotation.get('PartOfGroup','None')
        color = annotation.get('Color','#F4FA58')
        name = annotation.get('Name',f'Annotation {idx}')

        coordinates = []

        for coord in annotation.findall('./Coordinates/Coordinate'):
            order = int(coord.get('Order',0))
            x = (float(coord.get('X',0))-offset_x) / scale_factor
            y = (float(coord.get('Y',0))-offset_y) / scale_factor

            # 좌표 리스트 확장

            while len(coordinates)<= order:
                coordinates.append(None)
            coordinates[order]=[x,y]

        if annotation_type =='Rectangle' and len(coordinates) == 4:
            coordinates.append(coordinates[0])

        polygon = {
            'type':'Feature',
            'id':f"{name.replace(' ','_')}_{idx}",
            "geometry": {
                "type":"Polygon",
                "coordinates" : [coordinates]
            },
            'properties': {
                'objectType' : 'annotation',
                'isLocked': True
            }
        }

        if group_name != "None" and group_name in groups:
            polygon['propertires']['classification'] = {
                "name" : group_name,
                "colorRGB" : groups[group_name]['colorRGB']
            }

        geojson['features'].append(polygon)

    with open(output_geojson_path , 'w', encoding = 'utf-8') as f:
        json.dump(geojson, f, indent=2)

    print(f"변환 완료 : {output_geojson_path}")

def batch_convert(input_dir,output_dir,scale_factor=1.0, offset_x = 0, offset_y = 0):
    """디렉토리 내의 모든 ASAP XML 파일을 QuPath GeoJSON으로 변환"""
    os.makedirs(output_dir, exist_ok= True)

    xml_files = glob.glob(os.path.join(input_dir, "*.xml"))

    if not xml_files:
        print(f"디렉토리 '{input_dir}' 에서 XML 파일을 찾을 수 없습니다.")
        return
    
    for xml_file in xml_files:
        # 출력 파일 이름 생성
        basename = os.path.splitext(os.path.basename(xml_file))[0]
        output_file = os.path.join(output_dir, f"{basename}.geojson")

        try:
            asap_xml_to_geojson(xml_file, output_file,scale_factor, offset_x,offset_y)
        except Exception as e:
            print(f"파일 '{xml_file}' 처리 중 오류 발생 : {e}")

def main():
    parser = argparse.ArgumentParser(description = 'ASAP XML을 Qupath geojson으로 변환')
    parser.add_argument('input',help = '입력 XML 파일 또는 디렉토리')
    parser.add_argument('output',help = '출력 GeoJSON파일 또는 디렉토리')
    parser.add_argument('--scale',type = float, default = 1.0 ,help='좌표값 배율조정 (예 : 0.5는 두 배크기, 2.0은 절반크기)')
    parser.add_argument('--offset-x',type=float, default = 0 , help = 'X 좌표 오프셋')
    parser.add_argument('--offset-y',type=float, default = 0 , help = 'Y 좌표 오프셋')
    parser.add_argument('--batch', action = 'store_true',help = '디렉토리 일괄 처리 모드')

    args = parser.parse_args()

    if args.batch:
        batch_convert(args.input,args.output, args.scale, args.offset_x,args.offset_y)
    else:
        asap_xml_to_geojson(args.input, args.output, args.scale, args.offset_x,args.offset_y)

if __name__ == "__main__":
    main()


