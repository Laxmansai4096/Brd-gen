"""
Hugging Face Spaces Entrypoint for AI BRD Generator & Project Planner
Leverages Gradio SDK on Hugging Face Spaces (100% Free Tier, No Credit Card Required)
Mounts the FastAPI app and serves the full interactive workbench.
"""
import os
import sys

# Monkey-patch HfFolder into huggingface_hub for complete backwards compatibility
import huggingface_hub
if not hasattr(huggingface_hub, "HfFolder"):
    try:
        from huggingface_hub.utils import HfFolder
        huggingface_hub.HfFolder = HfFolder
    except ImportError:
        class DummyHfFolder:
            @staticmethod
            def get_token():
                return os.environ.get("HF_TOKEN", "")
            @staticmethod
            def save_token(token):
                pass
        huggingface_hub.HfFolder = DummyHfFolder

import gradio as gr
from app import app as fastapi_app


# Native Gradio application rendering the Workbench
with gr.Blocks(title="AI BRD Generator & Workbench", fill_height=True) as demo:
    with gr.Row():
        gr.Markdown("### ⚡ AI BRD Generator & Project Planner Workbench")
    with gr.Row():
        gr.HTML(
            """
            <iframe src="/static/index.html" width="100%" height="950px" style="border:none; width:100%; min-height:92vh; border-radius:8px;"></iframe>
            """
        )

# Mount FastAPI endpoints onto Gradio's internal ASGI router
for route in fastapi_app.routes:
    demo.app.routes.append(route)

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860, show_api=False)








