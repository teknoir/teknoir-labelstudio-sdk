# Import own images
images_path = 'data/ppe/anderscctv/unlabeled1'


def import_to_ls(current_blob):
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

    task = {
        'data': {
            'image': image_url
        },
        "file_upload": uploaded_file_ids[0],
        'annotations': []
    }

    # pprint(task)
    post_ls_task(task)


def import_images():
    print(f'### Read files in folder: gs://{bucket_name}/{images_path} ###')
    blobs = storage_client.list_blobs(bucket_name, prefix=f'{images_path}/', delimiter='/')
    for blob in blobs:
        if blob.name.endswith('.jpg'):
            blob = bucket.get_blob(blob.name)
            import_to_ls(blob)


import_images()