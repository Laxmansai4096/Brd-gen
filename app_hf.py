"""
Hugging Face Spaces Entrypoint for AI BRD Generator & Project Planner
Leverages Gradio SDK on Hugging Face Spaces (100% Free Tier, No Credit Card Required)
Mounts the FastAPI app routes directly into Gradio's internal FastAPI app.
"""
import gradio as gr
from app import app as fastapi_app

# Gradio interface embedding the full AI BRD workbench
with gr.Blocks(title="AI BRD Generator & Workbench", theme=gr.themes.Base()) as demo:
    gr.HTML(
        """
        <iframe src="/static/index.html" width="100%" height="950px" style="border:none; border-radius:12px; min-height:92vh; width:100%; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"></iframe>
        """
    )

# Mount all FastAPI routes, middleware, and static files onto Gradio's internal FastAPI app
# This guarantees single-port 7860 execution with zero port collisions on Hugging Face Spaces
for route in fastapi_app.routes:
    demo.app.routes.append(route)



