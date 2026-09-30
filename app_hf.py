"""
Hugging Face Spaces Entrypoint for AI BRD Generator & Project Planner
Leverages Gradio SDK on Hugging Face Spaces (100% Free Tier, No Credit Card Required)
Mounts the FastAPI app and serves the full interactive workbench.
"""
import os
import gradio as gr
from app import app as fastapi_app

# Gradio block exposing the workbench
with gr.Blocks(title="AI BRD Generator & Workbench", fill_height=True) as demo:
    gr.HTML(
        """
        <style>
          .gradio-container { padding: 0 !important; max-width: 100% !important; }
        </style>
        <iframe src="/static/index.html" width="100%" height="1000px" style="border:none; width:100%; min-height:95vh;"></iframe>
        """
    )

# Mount Gradio onto the existing FastAPI application
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Export demo for Hugging Face Spaces Gradio runner
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)







