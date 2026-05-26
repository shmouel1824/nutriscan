"""
core/ml/predictor.py
=====================
PyTorch inference module for Django.
Loaded ONCE at startup — not per request.
"""

import sys


import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b0
from PIL import Image
import json, requests
from io import BytesIO
from django.conf import settings

print(f"DEBUG ML_MODEL_PATH = {settings.ML_MODEL_PATH}", file=sys.stderr)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load class names
_class_names = json.loads(
    settings.ML_CLASS_NAMES_PATH.read_text(encoding='utf-8')
)

# Build model architecture (must match training)
def _build_model(num_classes):
    model = efficientnet_b0(weights=None)
    in_f  = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(in_f, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.3),
        nn.Linear(256, num_classes)
    )
    return model

# Load weights — once at startup
_model = _build_model(len(_class_names))
_model.load_state_dict(
    torch.load(settings.ML_MODEL_PATH, map_location=DEVICE)
)
_model.to(DEVICE).eval()

# Preprocessing transform
_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def predict_from_pil(pil_image, top_k=3):
    """Run inference on a PIL Image. Returns top_k predictions."""
    img    = pil_image.convert('RGB')
    tensor = _transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        probs = F.softmax(_model(tensor), dim=1)[0]
    top_p, top_i = probs.topk(top_k)
    return [
        {
            'food'       : _class_names[i].replace('_', ' ').title(),
            'food_key'   : _class_names[i],
            'confidence' : round(float(p) * 100, 1)
        }
        for p, i in zip(top_p.tolist(), top_i.tolist())
    ]

def predict_from_upload(django_file):
    """Accept a Django uploaded file and predict."""
    return predict_from_pil(Image.open(django_file))

def predict_from_url(url):
    """Download image from URL and predict — with browser headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        return predict_from_pil(img)
    except Exception as exc:
        raise ValueError(f"Could not load image from URL: {exc}")