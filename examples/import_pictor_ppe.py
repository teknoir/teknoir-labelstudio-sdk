import os
from google.cloud import storage
from tempfile import mkstemp
import numpy as np
from PIL import Image
from pathlib import Path
import teknoir_labelstudio_sdk

########## EDIT THIS ##############
namespace = 'boxer-property'
labelstudio_project = 'ppe-test'
owner = 'anders.aslund@teknoir.ai'
########## EDIT THIS ##############

bucket_name = f'{namespace}.teknoir.cloud'

# Read the crowdsourced Pictor PPE approach 2 dataset
pictor_ppe_image_path = 'data/ppe/pictor-ppe-crowdsourced/Images'
pictor_ppe_set_path = 'data/ppe/pictor-ppe-crowdsourced/Labels'
pictor_ppe_set_files = [
    'pictor_ppe_crowdsourced_approach-02_test.txt',
    'pictor_ppe_crowdsourced_approach-02_train.txt',
    'pictor_ppe_crowdsourced_approach-02_valid.txt'
]
pictor_ppe_filepath_dir = f'import/pictor-ppe/'
pictor_labels = ['W', 'WH', 'WV', 'WHV']
pictor_to_project_labels = {
    'W': 'worker',
    'WH': 'worker_hardhat',
    'WV': 'worker_vest',
    'WHV': 'worker_vest_hardhat'
}

storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)

# Connect to the Label Studio API and check the connection
ls = teknoir_labelstudio_sdk.Client(extra_headers=teknoir_labelstudio_sdk.jwt_header('anders.aslund@teknoir.ai'))
print(ls.check_connection())

projects = ls.list_projects(title=labelstudio_project)
project = projects[0]
print(project.parsed_label_config)


def pictor_to_project_label(idx):
    # ['W','WH','WV','WHV']
    # ["worker", "worker_vest", "worker_hardhat", "worker_vest_hardhat"]
    return pictor_to_project_labels[pictor_labels[idx]]


def pictor_to_ls_annotation(center_x, center_y, width, height, image_width, image_height):
    x = (center_x / image_width) * 100.0
    y = (center_y / image_height) * 100.0
    w = ((width / image_width) * 100.0) - x
    h = ((height / image_height) * 100.0) - y
    return x, y, w, h


def import_pictor_ppe_set(text):
    for line in text.splitlines():
        yolo_annotations = line.split();
        image_name = yolo_annotations.pop(0)

        current_blob = bucket.get_blob(f'{pictor_ppe_image_path}/{image_name}')
        _, temp_local_filename = mkstemp(prefix=Path(image_name).name, suffix=Path(image_name).suffix)
        current_blob.download_to_filename(temp_local_filename)
        print(f"Image {image_name} was downloaded to {temp_local_filename}.")

        img = np.array(Image.open(temp_local_filename).convert('RGB'))
        width = img.shape[1]
        height = img.shape[0]

        task_ids = project.import_tasks(temp_local_filename)
        print(f"Uploaded files task ids: {task_ids}")
        selected_tasks = project.get_tasks(selected_ids=task_ids)
        print(f"Selected tasks: {selected_tasks}")

        # Delete the temporary file.
        os.remove(temp_local_filename)

        task = selected_tasks[0]
        results = []
        while len(yolo_annotations) > 0:
            y_annotation = yolo_annotations.pop(0).split(',')
            x, y, w, h = pictor_to_ls_annotation(int(y_annotation[0]), int(y_annotation[1]), int(y_annotation[2]),
                                                 int(y_annotation[3]), width, height)
            label = pictor_to_project_label(int(y_annotation[4]))

            result = {
                'from_name': 'label',
                'source': '$image',
                'to_name': 'image',
                'type': 'rectanglelabels',
                'original_width': width,
                'original_height': height,
                'image_rotation': 0,
                'value': {
                    'rectanglelabels': [label],
                    'rotation': 0,
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                }
            }
            results.append(result)

        project.create_annotation(task_id=task['id'], result=results)


def import_pictor_ppe():
    for file in pictor_ppe_set_files:
        print(f'### Read file: gs://{bucket_name}/{pictor_ppe_set_path}/{file} ###')
        blob = bucket.get_blob(f'{pictor_ppe_set_path}/{file}')
        multiline_text = blob.download_as_text(encoding="utf-8")
        import_pictor_ppe_set(multiline_text)


import_pictor_ppe()
