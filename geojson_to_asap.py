import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os, glob, argparse

def is_rectanble(coordinates): 
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
