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
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)

# Connect to the Label Studio API and check the connection
ls = teknoir_labelstudio_sdk.Client(extra_headers=teknoir_labelstudio_sdk.jwt_header('anders.aslund@teknoir.ai'))
print(ls.check_connection())

projects = ls.list_projects(title=labelstudio_project)
project = projects[0]
print(project.parsed_label_config)

# Read the Kaggle Hardhat and Safety vest for Object Detection dataset

kaggle_hh_and_v_image_path = 'data/ppe/kaggle/hardhat-and-safety-vest-image-for-object-detection'
kaggle_labels = ['W', 'WH', 'WV', 'WHV']
kaggle_to_project_labels = {
    'W': 'worker',
    'WH': 'worker_hardhat',
    'WV': 'worker_vest',
    'WHV': 'worker_vest_hardhat'
}

def kaggle_to_project_label(idx):
    # ['W','WH','WV','WHV']
    # ["worker", "worker_vest", "worker_hardhat", "worker_vest_hardhat"]
    return kaggle_to_project_labels[kaggle_labels[idx]]


def yolo_to_ls_annotation(_x, _y, width, height):
    x = (_x - (width / 2.0)) * 100.0
    y = (_y - (height / 2.0)) * 100.0
    w = width * 100.0
    h = height * 100.0
    return x, y, w, h


def import_kaggle_task(current_blob, text):
    _, temp_local_filename = mkstemp(prefix=Path(current_blob.name).name, suffix=Path(current_blob.name).suffix)
    current_blob.download_to_filename(temp_local_filename)
    print(f"Image {current_blob.name} was downloaded to {temp_local_filename}.")

    img = np.array(Image.open(temp_local_filename).convert('RGB'))
    width = img.shape[1]
    height = img.shape[0]

    task_ids = project.import_tasks(temp_local_filename)
    selected_tasks = project.get_tasks(selected_ids=task_ids)
    task = selected_tasks[0]

    # Delete the temporary file.
    os.remove(temp_local_filename)

    results = []
    print(text)
    for line in text.splitlines():
        a = line.split();

        if len(a) > 0:
            label = kaggle_to_project_label(int(a[0]))
            x, y, w, h = yolo_to_ls_annotation(float(a[1]), float(a[2]), float(a[3]), float(a[4]))

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

        print(results)
        project.create_annotation(task_id=task['id'], result=results)


def import_kaggle_hardhat_and_vest_dataset():
    print(f'### Read files in folder: gs://{bucket_name}/{kaggle_hh_and_v_image_path} ###')
    blobs = storage_client.list_blobs(bucket_name, prefix=f'{kaggle_hh_and_v_image_path}/', delimiter='/')
    for blob in blobs:
        blob = bucket.get_blob(blob.name)
        multiline_text = ""
        if blob.name.endswith('.jpg'):
            p = Path(blob.name)
            annotation_file = p.with_name(p.stem).with_suffix('.txt')
            print(f'Trying to read: gs://{bucket_name}/{annotation_file}')
            text_blob = bucket.get_blob(f'{annotation_file}')
            if text_blob.exists():
                print(f'...read')
                multiline_text = text_blob.download_as_text(encoding="utf-8")
            import_kaggle_task(blob, multiline_text)
        if blob.name.endswith('.png'):
            p = Path(blob.name)
            annotation_file = p.with_name(p.stem).with_suffix('.txt')
            print(f'Trying to read: gs://{bucket_name}/{annotation_file}')
            text_blob = bucket.get_blob(f'{annotation_file}')
            if text_blob.exists():
                print(f'...read')
                multiline_text = text_blob.download_as_text(encoding="utf-8")
            import_kaggle_task(blob, multiline_text)


import_kaggle_hardhat_and_vest_dataset()
