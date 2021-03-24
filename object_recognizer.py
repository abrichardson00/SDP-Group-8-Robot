import os
from google.cloud import vision

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="blahblah path to json"

def localize_objects(path):
    """Localize objects in the local image.

    Args:
    path: The path to the local file.
    """
    #from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with open(path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    objects = client.object_localization(
        image=image).localized_object_annotations

    print('Number of objects found: {}'.format(len(objects)))
    for object_ in objects:
        print('\n{} (confidence: {})'.format(object_.name, object_.score))
        print('Normalized bounding polygon vertices: ')
        for vertex in object_.bounding_poly.normalized_vertices:
            print(' - ({}, {})'.format(vertex.x, vertex.y))
    return [object_.name.lower() for object_ in objects]

def detect_text(path):
    """Detects text in the file."""
    #from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    return [text.description.lower() for text in texts]

# only bother with something like this if we really need it
""" 
def remove_small_texts(texts, threshold_area):
    filtered_text_list = []
    # only include texts who's bounding box is big enough
    for text in texts:
        br,tl = text.bounding_poly.vertices[1], text.bounding_poly.vertices[3]
        area = (br.x - tl.x)*(br.y - tl.y)
        #if area > threshold_area:
        filtered_text_list.append(text.description)
    return filtered_text_list
"""


def get_tray_info(path):
    detected_text = detect_text(path)
    detected_objects = localize_objects(path)
    return detected_text + detected_objects

