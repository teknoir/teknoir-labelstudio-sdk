import chevron
import os
import teknoir_labelstudio_sdk
import zipfile
import json
from random import shuffle
from pathlib import Path
from google.cloud import storage
from urllib.parse import urlparse
import tarfile

########## EDIT THIS ##############
namespace = 'boxer-property'
domain = 'teknoir.cloud'
labelstudio_project = 'ppe-test'
labels = ["worker", "worker_vest", "worker_hardhat", "worker_vest_hardhat"]
workspace = 'workspace'
config_template_url = 'gs://boxer-property.teknoir.cloud/transfer-learning/yolov7/cfg/yolov7-tiny-config-template.yaml'
transfer_weights_url = 'gs://boxer-property.teknoir.cloud/transfer-learning/yolov7/weights/yolov7_training.pt'
hyp_file_url = 'gs://boxer-property.teknoir.cloud/transfer-learning/yolov7/hyp/hyp.scratch.tiny.yaml'
########## EDIT THIS ##############

def prepare_labelstudio_data_for_yolo(
        project: str,
        labels: list,
        namespace: str,
        domain: str,
        config_template_url: str,
        transfer_weights_url: str,
        hyp_file_url: str,
        train_frac: float,
        validate_frac: float):
    '''
    Prepares Labelstudio Data for YOLO training
    Example weights_url: https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7_training.pt
    '''

    print(f'Prepares Labelstudio Data for training of YOLOv7')

    def create_directory(directory_name, basedir=None):
        if basedir is None:
            pth = Path(directory_name)
        else:
            pth = Path(os.path.join(basedir, directory_name))
        pth.mkdir(parents=True, exist_ok=True)
        return pth.as_posix()

    # Directory structure
    basedir = create_directory(workspace)  # /workspace
    configdir = create_directory('config', basedir)  # /workspace/model
    datadir = create_directory('dataset', basedir)  # /workspace/dataset
    imagesdir = create_directory('images', datadir)  # /workspace/dataset/images
    trainimagesdir = create_directory('train', imagesdir)  # /workspace/dataset/images/train
    valimagesdir = create_directory('val', imagesdir)  # /workspace/dataset/images/val
    testimagesdir = create_directory('test', imagesdir)  # /workspace/dataset/images/test
    labelsdir = create_directory('labels', datadir)  # /workspace/dataset/labels
    trainlabelsdir = create_directory('train', labelsdir)  # /workspace/dataset/labels/train
    vallabelsdir = create_directory('val', labelsdir)  # /workspace/dataset/labels/val
    testlabelsdir = create_directory('test', labelsdir)  # /workspace/dataset/labels/test

    # Connect to the Label Studio API and check the connection
    ls = teknoir_labelstudio_sdk.Client(
        extra_headers=teknoir_labelstudio_sdk.jwt_header('kubeflow.training@teknoir.ai'))
    print(ls.check_connection())

    projects = ls.list_projects(title=project)
    p = projects[0]
    print(p.parsed_label_config)

    yolo_annotations_file_zip = p.export_tasks(export_type="YOLO", download_resources=True,
                                                     export_location=f'{workspace}/{project}.zip')

    tasks_json_file = p.export_tasks(export_type="JSON", download_resources=True,
                                           export_location=f'{workspace}/{project}.json')

    with open(tasks_json_file) as f:
        tasks = json.load(f)

    if len(tasks) == 0:
        print(f'NO TASKS FOUND FOR {project}')
        exit(0)

    ind_list = list(range(len(tasks)))
    shuffle(ind_list)
    test_frac = 1.0 - train_frac - validate_frac
    train_set = ind_list[:int((len(ind_list) + 1) * train_frac)]
    test_set = ind_list[int((len(ind_list) + 1) * train_frac):int((len(ind_list) + 1) * (train_frac + test_frac))]
    val_set = ind_list[int((len(ind_list) + 1) * (train_frac + test_frac)):]

    print(f'Number of tasks: {len(tasks)}')
    print(f'Train set size: {len(train_set)}')
    print(f'Validate set size: {len(test_set)}')
    print(f'Test set size: {len(val_set)}')

    bucket_name = f'{namespace}.{domain}'
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    labelstudio_upload_location = 'label-studio/data'

    with zipfile.ZipFile(yolo_annotations_file_zip, 'r') as zip_ref:
        zip_ref.extractall(f'{workspace}/{project}/yolo')

    yolo_labelsdir = f'{workspace}/{project}/yolo/labels'

    # DATA SETS
    def write_dataset(tasks, set, imagesdir, labelsdir):
        for i in set:
            task = tasks[i]
            if task['data']['image']:
                image_path = task['data']['image']
                image_name = Path(image_path).name
                source_image = f'{labelstudio_upload_location}/{image_path}'
                dest_image = f'{imagesdir}/{image_name}'
                current_blob = bucket.get_blob(source_image)
                current_blob.download_to_filename(dest_image)
                print(f"Image {image_name} was downloaded to {dest_image}.")

                source_labels = f'{yolo_labelsdir}/{Path(image_name).stem}.txt'
                dest_labels = f'{labelsdir}/{Path(image_name).stem}.txt'
                os.rename(source_labels, dest_labels)
                print(f"Moved labels from {source_labels} to {dest_labels}.")

    # Write training dataset
    write_dataset(tasks, train_set, trainimagesdir, trainlabelsdir)

    # Write validation dataset
    write_dataset(tasks, val_set, valimagesdir, vallabelsdir)

    # Write test dataset
    write_dataset(tasks, test_set, testimagesdir, testlabelsdir)

    # CONFIG
    print(f"Writing CONFIG file")
    data_file = os.path.join(configdir, f'data.yaml')
    print(f"- DST: {data_file}")

    num_classes = len(labels)

    names_file = os.path.join(datadir, "object.names")
    train_data_file = os.path.join(datadir, "train.txt")
    val_data_file = os.path.join(datadir, "val.txt")
    test_data_file = os.path.join(datadir, "test.txt")

    with open(data_file, 'w') as out:
        out.write(f'train: {train_data_file}\n')
        out.write(f'val: {val_data_file}\n')
        out.write(f'test: {test_data_file}\n')
        out.write(f'nc: {num_classes}\n')
        out.write(f'names: [{", ".join(labels)}]')

    with open(names_file, 'w') as out:
        for l in labels:
            out.write(l + '\n')

    # /workspace/dataset/train.txt
    with open(train_data_file, 'w') as out:
        for f in os.listdir(trainimagesdir):
            out.write(f'{os.path.join(trainimagesdir, f)}\n')

    # /workspace/dataset/val.txt
    with open(val_data_file, 'w') as out:
        for f in os.listdir(valimagesdir):
            out.write(f'{os.path.join(valimagesdir, f)}\n')

    # /workspace/dataset/test.txt
    with open(test_data_file, 'w') as out:
        for f in os.listdir(testimagesdir):
            out.write(f'{os.path.join(testimagesdir, f)}\n')

    # CONFIG (from GCS)
    print(f"Writing YOLOv7 CONFIG file")
    print(f"- SRC: {config_template_url}")
    custom_config_file = os.path.join(configdir, "config.yaml")
    print(f"- DST: {custom_config_file}")
    parsed_url = urlparse(config_template_url)
    blob = bucket.blob(parsed_url.path[1:])
    with open(custom_config_file, 'w') as fout:
        parsed_config = chevron.render(blob.download_as_string().decode(),
                                       {"num_classes": num_classes})
        # to configure anything else, create a copy, modify, and reference.
        # full parameterization would likely be more confusing than helpful
        fout.write(parsed_config)
        print(parsed_config)

    # HYP FILE (from GCS)
    print("Copying HYP file")
    print(f"- SRC: {hyp_file_url}")
    hyp_file = os.path.join(configdir, "hyp.yaml")
    print(f"- DST: {hyp_file}")
    parsed_url = urlparse(hyp_file_url)
    blob = bucket.blob(parsed_url.path[1:])
    blob.download_to_filename(hyp_file)

    # PRETRAINED WEIGHTS (from GCS)
    if transfer_weights_url:
        print(f"Copying weights for transfer learning")
        print(f"- SRC: {transfer_weights_url}")
        transfer_weights_file = os.path.join(configdir, 'transfer_weights.pt')
        print(f"- DST: {transfer_weights_file}")
        parsed_url = urlparse(transfer_weights_url)
        blob = bucket.blob(parsed_url.path[1:])
        blob.download_to_filename(transfer_weights_file)

    # COMPRESS WORKSPACE
    def make_tarfile(output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    make_tarfile('yolo_training_workspace.tgz', basedir)



prepare_labelstudio_data_for_yolo(labelstudio_project, labels, namespace, domain, config_template_url, transfer_weights_url, hyp_file_url, 0.8, 0.1)
