import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os, glob, argparse

def is_rectangle(coordinates): 
    """주어진 좌표가 사각형인지 확인하기"""
    """QuPath의 경우 사각형의 좌표가 점 4개가 아니라 5개로 표현되는 경우가 있음."""
    # 첫 번째와 마지막 좌표가 동인한지 확인
    bool_ty = True
    if coordinates[0] != coordinates[4] and len(coordinates)!=5:
        return False, False
    
    x0,y0 = coordinates[0]
    x1,y1 = coordinates[1]
    x2,y2 = coordinates[2]
    x3,y3 = coordinates[3]

    edges_parallel = (
        (x0 == x3 and y1 == y2) or
        (y0 == y1 and x2 == x3)
    )
    return coordinates[:4], bool_ty

def prettify_xml(elem):
    """XML 요소를 예쁘게 들여쓰기하여 문자열로 반환"""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='\t', encoding = 'utf-8')

def geojson_to_asap_xml(geojson_path, output_xml_path, group_name = 'Unknown',
                        group_color='#F4FA58', offset_x = 0 ,offset_y = 0, scale_factor=1,
                          target_names = None, type_names = None):
    # GEOjson 파일 로드 (qupath 포멧)
    with open(geojson_path,'r',encoding='utf-8') as f:
        data = json.load(f)
    features = []
    if 'type' in data and data['type'] == 'Feature':
        features = [data]
    elif 'features' in data:
        features = data['features']
    else:
        print('지원되지 않는 GeoJson 입니다.')
        return
    
    # ASAP XML 구조 생성
    root = ET.Element('ASAP_ANnotations')
    annotations = ET.SubElement(root,'Annotations')

    # 처리된 그룹 추적
    groups_set = set()
    if group_name:
        groups_set.add(group_name)
    for idx, feature in enumerate(features):
        try:
            cls1 = feature.get('properties').get('classification').get('names')
        except:
            cls1 = False
        properties = feature.get('properties' , {})
        geometry = feature.get('geometry' , {})
        geometry_type = geometry.get('type','')

        if geometry_type != 'Polygon':
            print(f"지원되지 않는 geometry 유형 : {geometry_type}, 건너뜁니다.")

        rt = is_rectangle(geometry['coordinates'][0])

        annotation = ET.SubElement(annotations, 'Annotation')
        """geometry에서 특정 이름만 가져오기"""
        try:
            if type(target_names) != bool and type(cls1) != bool and cls1 != None and len(cls1) > 1:
                if cls1[0] in type_names and cls1[1] in target_names:
                    cls_name = '_'.join(cls1)
                    annotation.set("Name", f"{cls_name}_{idx}")
                else:
                    print(cls1[0] in type_names, cls1[1] in target_names)
                    annotation.set('Name',f'Annotation {idx}')
            else:
                annotation.set('Name',f'Annotation {idx}')
        except:
            print(target_names, cls1)
        if rt[1]: # 사각형이냐?
            annotation.set('Type','Rectangle')
            geometry['coordinates'][0] = rt[0]
        else:
            annotation.set('Type','Spline')

        annotation.set('PartOfGroup','None')

        annoation.set('Color', group_color)

        coords = ET.SubElement(annotation,'Coordinates')

        for coord_idx, coord in enumerate(geometry['coordinates'][0]):
            coordinate = ET.SubElement(coords, 'Coordinate')
            coordinate.set('Order',str(coord_idx))

            x = float(coord[0]) * scale_factor + offset_x
            y = float(coord[1]) * scale_factor + offset_y


            coordiante.set('X',f'{x:.4f}')
            coordinate.set('Y',f'{y:.4f}')

    groups_element = ET.SubElement(root,'AnnotationGroups')

    for group_name in groups_set:
        group = ET.SubElement(groups_element, "Group")
        group.set('Name',group_name)
        group.set('PartOfGroup',"None")
        group.set("Color", group_color)

        attributes = ET.SubElement(group, "Attributes")

    pretty_xml = prettify_xml(root)

    with open(outptu_xml_path, 'wb') as f:
        f.write(pretty_xml)
    print(f"변환 완료: {output_xml_path}")

def batch_convert(input_dir,oupput_dir, group_name = 'Unknown', group_color='#F4FA58'):
    """디렉토리 내의 모든 GeoJson 파일을 ASAP XML로 변환"""
    os.makedirs(output_dir,exist_ok =True)

    # 모든 GeoJson 파일 찾기
    geojson_files = glob.glob(os.path.join(input_dir,"*.geojson"))
    geojson_files.extend(glob.glob(os.path.join(input_dir, "*.json")))

    try:
        geojson_to_asap_xml(geojson_files,output_file,group_name,group_color)
    except Exception as e:
        print(f"파일 '{geojson_files}' 처리 중 오류 발생")

def main():
    parser = argparse.ArgumentParser(description = 'Qupath GeoJson을 ASAP XML로 변환')
    parser.add_argument('input',help='입력 GeoJSON 파일 또는 디렉토리')
    parser.add_argument("output", help="출력 XML 파일 또는 디렉토리")
    parser.add_argument("--group",default='Unknown',help = '주석 그룹 이름')
    parser.add_argument("--color", default = "#F4FA58", help = '주석 색상 (예 : #64FE2E)')
    # parser.add_argument("--scale", type = float, default=1.0, help = '좌표값 배율 조정 (예: 0.5는 절반크기, 2.0은 두배 크기)') ## 기능 추가하기
    parser.add_argument('--batch', action='store_true',help= '디렉토리 일괄 처리 모드')
    
    args = parser.parse_args()

    if args.batch:
        batch_convert(args.input, args.output, args.group, args.color, args.scale)
    else:
        geojson_to_asap_xml(args.input,args.output,args.group, args.color,args.scale)

if __name__ == "__main__":
    main()
    


