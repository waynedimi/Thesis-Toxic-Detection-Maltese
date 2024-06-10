import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import numpy as np
import gradio as gr
from PIL import ImageGrab
import os

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_model_and_tokenizer(model_path, model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.save_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    return tokenizer, model

def preprocess_text(tokenizer, text):
    encodings = tokenizer([text], truncation=True, padding=True, max_length=128, return_tensors='pt')
    return encodings['input_ids'].to(device), encodings['attention_mask'].to(device)

def classify_text(text, model_name, model_path, model_base):
    tokenizer, model = load_model_and_tokenizer(model_path, model_base)
    input_ids, attention_mask = preprocess_text(tokenizer, text)
    
    model.eval()
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits.squeeze()
        prediction = torch.sigmoid(logits).detach().cpu().numpy()
        prediction = (prediction > 0.5).astype(int)
    
    return "Toxic" if prediction == 1 else "Non-toxic"

# Cross-validation models
models_validation = [
    ('BERT', './models/Experiments/Validation/Experiment-1/BERT_ENG', 'bert-base-uncased'),
    ('XLMR', './models/Experiments/Validation/Experiment-1/XLM-R_ENG', 'xlm-roberta-base'),
    ('RoBERTa' , './models/Experiments/Validation/Experiment-1/RoBERTa_ENG' , 'FacebookAI/roberta-base'),
    ('mBERTu' , './models/Experiments/Validation/Experiment-1/mBERTu_ENG' , 'MLRS/mBERTu'),
    ('BERT_FT', './models/Experiments/Validation/Experiment-2/BERT_FT', 'bert-base-uncased'),
    ('XLMR_FT', './models/Experiments/Validation/Experiment-2/XLM-R_FT', 'xlm-roberta-base'),
    ('RoBERTa_FT' , './models/Experiments/Validation/Experiment-2/RoBERTa_FT' , 'FacebookAI/roberta-base'),
    ('mBERTu_FT', './models/Experiments/Validation/Experiment-2/mBERTu_FT', 'MLRS/mBERTu'),
]

def classify_text_with_model_cross_validation(text, model_choice):
    for model_name, model_path, model_base in models_validation:
        if model_choice == model_name:
            return classify_text(text, model_name, model_path, model_base)

def save_test_case(text, model_choice, classification):
    if not os.path.exists("test_cases"):
        os.makedirs("test_cases")
    test_case_id = len(os.listdir("test_cases")) + 1
    file_path = f"test_cases/TestCase{test_case_id}.png"
    
    # Capture the UI portion for the test case
    bbox = (100, 100, 1200, 600)  # Adjust the bbox as per your UI layout
    screenshot = ImageGrab.grab(bbox)
    screenshot.save(file_path)

model_names_cross_validation = [model[0] for model in models_validation]

with gr.Blocks(css="body {background-color: #2d2d2d; color: white;} .gradio-container {padding: 20px;} .gradio-container .input-output {margin-bottom: 10px;}") as interface:
    gr.Markdown("# Toxicity Classifier")
    
    with gr.Tab("Models"):
        gr.Markdown("Classify text as Toxic or Non-toxic using models.")
        text_input_cv = gr.Textbox(lines=2, placeholder="Enter text here...", label="Textbox", elem_id="input-output")
        model_dropdown_cv = gr.Dropdown(choices=model_names_cross_validation, label="Choose Model", elem_id="input-output")
        classify_button_cv = gr.Button("Classify", elem_id="input-output")
        output_cv = gr.Textbox(label="Result", elem_id="input-output")

        def classify_and_save(text, model):
            classification = classify_text_with_model_cross_validation(text, model)
            save_test_case(text, model, classification)
            return classification

        classify_button_cv.click(fn=classify_and_save, inputs=[text_input_cv, model_dropdown_cv], outputs=output_cv)

if __name__ == "__main__":
    interface.launch()
