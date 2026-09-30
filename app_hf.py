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

# Mount Gradio app into FastAPI under /gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Main execution for Hugging Face Spaces
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app_hf:fastapi_app", host="0.0.0.0", port=port)

