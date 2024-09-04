# Read the Kaggle Hardhat Detection dataset
from lxml import objectify

kaggle_hh_path = 'data/ppe/kaggle/hard-hat-detection'
kaggle_hh_images_path = 'images'
kaggle_hh_annotations_path = 'annotations'


def kaggle_hardhat_to_label(name):
    # labels = ["worker", "worker_vest", "worker_hardhat", "worker_vest_hardhat"]
    if name == 'helmet':
        return labels[2]
    if name == 'head':
        return labels[0]
    if name == 'person':
        return labels[0]
    return ''


def kaggle_hardhat_to_ls_annotation(o, width, height, label):
    x = (int(o.bndbox.xmin) / width) * 100.0
    y = (int(o.bndbox.ymin) / height) * 100.0
    w = ((int(o.bndbox.xmax) / width) * 100.0) - x
    h = ((int(o.bndbox.ymax) / height) * 100.0) - y
    return {
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


def import_pictor_kaggle_hardhat(current_blob, text):
    _, temp_local_filename = mkstemp()
    current_blob.download_to_filename(temp_local_filename)
    print(f"Image {current_blob.name} was downloaded to {temp_local_filename}.")

    # Normalize image name
    image_name = re.sub('[^A-Za-z0-9\.]+', '_', Path(current_blob.name).name)

    uploaded_file_ids = post_import_image(temp_local_filename, image_name)
    print(f"Uploaded file ids: {uploaded_file_ids}")
    uploaded_files = get_imported_image(uploaded_file_ids)

    image_url = f'{api_image_destination_url}{uploaded_files[0]["file"]}'
    print(f"Imported image location: {image_url}")

    # Delete the temporary file.
    os.remove(temp_local_filename)

    annotation = objectify.fromstring(text)
    width = annotation.size.width
    height = annotation.size.height
    results = []
    for o in annotation.object:
        label = kaggle_hardhat_to_label(o.name)
        if label:
            results.append(kaggle_hardhat_to_ls_annotation(o, int(width), int(height), label))

    task = {
        'data': {
            'image': image_url
        },
        "file_upload": uploaded_file_ids[0],
        'annotations': [{
            'created_username': owner,
            'result': results
        }]
    }

    # pprint(task)
    post_ls_task(task)


def import_kaggle_hardhat():
    print(f'### Read files in folder: gs://{bucket_name}/{kaggle_hh_path}/{kaggle_hh_images_path} ###')
    blobs = storage_client.list_blobs(bucket_name, prefix=f'{kaggle_hh_path}/{kaggle_hh_images_path}/', delimiter='/')
    for blob in blobs:
        blob = bucket.get_blob(blob.name)
        multiline_text = ""
        if blob.name.endswith('.jpg'):
            p = Path(blob.name)
            annotation_file = f'{kaggle_hh_path}/{kaggle_hh_annotations_path}/{p.with_name(p.stem).with_suffix(".xml").name}'
            print(f'Trying to read: gs://{bucket_name}/{annotation_file}')
            text_blob = bucket.get_blob(f'{annotation_file}')
            if text_blob.exists():
                print(f'...read')
                multiline_text = text_blob.download_as_text(encoding="utf-8")
            import_pictor_kaggle_hardhat(blob, multiline_text)
        if blob.name.endswith('.png'):
            p = Path(blob.name)
            annotation_file = f'{kaggle_hh_path}/{kaggle_hh_annotations_path}/{p.with_name(p.stem).with_suffix(".xml").name}'
            print(f'Trying to read: gs://{bucket_name}/{annotation_file}')
            text_blob = bucket.get_blob(f'{annotation_file}')
            if text_blob.exists():
                print(f'...read')
                multiline_text = text_blob.download_as_text(encoding="utf-8")
            import_pictor_kaggle_hardhat(blob, multiline_text)


import_kaggle_hardhat()