import os
import torch
import gdown
import streamlit as st
from transformers import ElectraForSequenceClassification, ElectraTokenizer

@st.cache_resource
def load_model_and_tokenizer_from_drive(file_id, num_labels=3):
    dest_path = "models/kcbert_max.pt"
    os.makedirs("models", exist_ok=True)

    # Google Drive에서 모델 다운로드
    if not os.path.exists(dest_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        with st.spinner("📥 모델 다운로드 중..."):
            gdown.download(url, dest_path, quiet=False)

    # 모델 및 토크나이저 로딩 (KoELECTRA + 3 클래스)
    tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-discriminator")
    model = ElectraForSequenceClassification.from_pretrained(
        "monologg/koelectra-base-discriminator", num_labels=num_labels
    )
    model.load_state_dict(torch.load(dest_path, map_location="cpu"))
    model.eval()

    return model, tokenizer
