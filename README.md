# Teknoir Label Studio SDK

A wrapper for the Label Studio SDK to run inside a Teknoir Notebook.

## Installation

```bash
sudo pip install git+git://github.com/teknoir/teknoir-labelstudio-sdk.git#egg=teknoir-labelstudio-sdk
```

## Usage

This library is intended to run inside a Teknoir Notebook, but can also be run locally.
Follow the [Label Studio documentation](https://labelstud.io/guide/sdk) for more information on how to use the SDK.

### Teknoir Notebook

```python
import teknoir_labelstudio_sdk
# Connect to the Label Studio API and check the connection
ls = teknoir_labelstudio_sdk.Client(extra_headers=teknoir_labelstudio_sdk.jwt_header('your.name@teknoir.ai'))
print(ls.check_connection())
```

### Local

In a separate terminal:
```bash
k port-forward svc/label-studio 8080:80
```
    
```python
import teknoir_labelstudio_sdk
# Connect to the Label Studio API and check the connection
ls = teknoir_labelstudio_sdk.Client(url='http://localhost:8080', extra_headers=teknoir_labelstudio_sdk.jwt_header('your.name@teknoir.ai'))
print(ls.check_connection())
```

## Examples

### Import Pictor PPE

In a separate terminal:
```bash
k port-forward svc/label-studio 8080:80
```

Run the example:
```bash
LABEL_STUDIO_URL=http://localhost:8080 GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/teknoir-admin-credentials.json GOOGLE_CLOUD_PROJECT=teknoir python examples/import_pictor_ppe.py
```
