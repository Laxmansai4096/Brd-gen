"""
Hugging Face Spaces Entrypoint for AI BRD Generator & Project Planner
Leverages Gradio SDK on Hugging Face Spaces (100% Free Tier, No Credit Card Required)
Mounts the FastAPI app directly into Gradio to serve both the interactive workbench
and the complete deterministic calculation/export engines.
"""
import os
import gradio as gr
from app import app as fastapi_app

# Gradio interface embedding the full AI BRD workbench
with gr.Blocks(title="AI BRD Generator & Workbench", theme=gr.themes.Base()) as demo:
    gr.HTML(
        """
        <iframe src="/static/index.html" width="100%" height="950px" style="border:none; border-radius:12px; min-height:92vh; width:100%; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"></iframe>
        """
    )

# Mount FastAPI app onto Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# On Hugging Face Spaces with 'sdk: gradio', HF automatically looks for 'demo'
# and launches it on port 7860. If executed directly as a script:
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)), app_kwargs={"docs_url": None})


