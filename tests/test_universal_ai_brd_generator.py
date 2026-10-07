import pytest
from backend.models import ProjectSession, AnswerItem
from backend.agent_planner import (
    detect_project_domain,
    generate_technical_components_dynamic,
    generate_sizing_and_bom_dynamic,
    generate_brd
)
from backend.agent_discovery import (
    process_user_answer,
    calculate_discovery_confidence,
    extract_and_fill_domains_from_text,
    get_all_reference_doc_questions
)

def test_universal_ai_domain_detection():
    """Verify all 5 AI disciplines & sub-domains are accurately classified."""
    # 1. Computer Vision
    assert detect_project_domain("Automated PCB surface defect detection and crack identification on manufacturing assembly lines.") == "cv_defect_detection"
    assert detect_project_domain("Real-time CCTV camera object detection and traffic surveillance tracking using YOLOv8.") == "cv_object_detection"
    assert detect_project_domain("Scanned invoice OCR and LayoutLM form document extraction.") == "cv_ocr_document"
    
    # 2. Deep Learning & Speech
    assert detect_project_domain("Contact center call recording speech-to-text transcription and audio analytics.") == "dl_speech_voice"
    assert detect_project_domain("Custom deep neural network for multi-layer signal processing.") == "dl_custom_neural"
    
    # 3. Classical Machine Learning
    assert detect_project_domain("Retail inventory demand planning and time-series sales forecasting.") == "ml_forecasting_timeseries"
    assert detect_project_domain("Banking transaction fraud detection and AML anti-money laundering anomaly detection.") == "ml_fraud_anomaly"
    assert detect_project_domain("E-commerce product recommendation and personalized two-tower ranking engine.") == "ml_recommendation"
    assert detect_project_domain("Telecom customer churn prediction using tabular XGBoost classifier.") == "ml_predictive_tabular"
    
    # 4. Natural Language Processing
    assert detect_project_domain("Multilingual NER named entity recognition and customer sentiment analysis using DeBERTa.") == "nlp_text_analytics"
    
    # 5. Generative AI
    assert detect_project_domain("Automated contract clause extraction and 3-tier legal risk assessment.") == "contract_intelligence"
    assert detect_project_domain("Customer support conversational chatbot and virtual helpdesk assistant.") == "customer_support"
    assert detect_project_domain("Enterprise RAG knowledge base search over documentation and internal wikis.") == "genai_rag_knowledge"
    assert detect_project_domain("Autonomous multi-agent orchestration and workflow execution.") == "genai_agentic_workflow"

def test_multi_cloud_technical_components_and_bom():
    """Verify dynamic technical components (C001-C006) and BoM generation across all 5 clouds."""
    clouds = ["AWS", "Azure", "GCP", "IBM Cloud", "Hybrid / On-Prem"]
    
    # Test CV on Hybrid / On-Prem
    onprem_comps = generate_technical_components_dynamic("Hybrid / On-Prem", "cv_defect_detection", "Defect AI")
    assert len(onprem_comps) == 6
    assert "Triton Inference Server" in onprem_comps[2].technology_choice or "Local GPU" in onprem_comps[2].technology_choice
    assert "MinIO" in onprem_comps[0].technology_choice
    
    metrics_onprem, bom_onprem = generate_sizing_and_bom_dynamic("Hybrid / On-Prem", "PoC", "Standard Non-HA", 20, 5, 2000)
    assert len(bom_onprem) >= 5
    assert any("MinIO" in b.component or "MinIO" in b.sku_or_service for b in bom_onprem)
    
    # Test ML on AWS
    aws_comps = generate_technical_components_dynamic("AWS", "ml_predictive_tabular", "Churn Predictor")
    assert len(aws_comps) == 6
    assert "SageMaker" in aws_comps[2].technology_choice
    
    metrics_aws, bom_aws = generate_sizing_and_bom_dynamic("AWS", "PoC", "Standard Non-HA", 20, 5, 2000)
    assert any("Amazon" in b.sku_or_service or "AWS" in b.sku_or_service for b in bom_aws)
    
    # Test Speech DL on GCP
    gcp_comps = generate_technical_components_dynamic("GCP", "dl_speech_voice", "Voice Intelligence")
    assert len(gcp_comps) == 6
    assert "Speech-to-Text" in gcp_comps[0].technology_choice or "Vertex AI" in gcp_comps[0].technology_choice
    
    # Test NLP on IBM Cloud
    ibm_comps = generate_technical_components_dynamic("IBM Cloud", "nlp_text_analytics", "Watson NLP")
    assert len(ibm_comps) == 6
    metrics_ibm, bom_ibm = generate_sizing_and_bom_dynamic("IBM Cloud", "PoC", "Standard Non-HA", 20, 5, 2000)
    assert any("IBM" in b.sku_or_service or "Watson" in b.sku_or_service for b in bom_ibm)

def test_ambiguous_user_response_handling_and_disambiguation():
    """Verify that ambiguous, brief, or open-ended inputs trigger intelligent disambiguation."""
    session = ProjectSession(session_id="universal-test-sess")
    
    # Step 1: User gives an ambiguous problem statement
    vague_input = "we want some AI system"
    msg, is_done = process_user_answer(session, vague_input, persona="CLIENT")
    
    # Verify agent does NOT hallucinate; it detects ambiguity and offers tailored blueprints/options
    assert not is_done
    assert session.clarification_state is not None or (msg.hitl_options and len(msg.hitl_options) > 0)
    
    # Step 2: User clarifies by choosing Option A (Knowledge & Policy Q&A Assistant)
    msg2, is_done2 = process_user_answer(session, "Build an Internal Enterprise Knowledge & Policy Q&A Assistant that indexes SharePoint/Blob PDF documents to answer employee questions and reduce HR/IT helpdesk ticket volume.", persona="CLIENT")
    first_ans = list(session.answers.values())[0]
    assert "Knowledge" in first_ans.answer or "Triage" in first_ans.answer
    assert first_ans.answer != "we want some AI system"

def test_full_brd_generation_all_5_disciplines():
    """Verify complete BRD generation for 5 distinct AI projects across different clouds."""
    testcases = [
        ("Acme Vision Corp", "Surface defect detection on manufacturing silicon wafers", "GCP", "cv_defect_detection"),
        ("Global FinBank", "Credit default and fraud risk tabular prediction using historical transactions", "AWS", "ml_fraud_anomaly"),
        ("CallCenter Pro", "Contact center audio speech-to-text transcription and sentiment analysis", "Azure", "dl_speech_voice"),
        ("GovAgency Legal", "Contract clause extraction and 3-tier contracting principle risk assessment", "Azure", "contract_intelligence"),
        ("Enterprise Search Ltd", "Multilingual entity extraction and semantic knowledge search across documentation", "IBM Cloud", "genai_rag_knowledge"),
    ]
    
    for client, problem, cloud, expected_domain in testcases:
        session = ProjectSession(session_id=f"sess-{expected_domain}")
        session.answers["q_client"] = AnswerItem(question_id="q_client", question_title="Client", answer=client)
        session.answers["q_problem"] = AnswerItem(question_id="q_problem", question_title="Problem", answer=problem)
        session.answers["q_cloud"] = AnswerItem(question_id="q_cloud", question_title="Cloud", answer=cloud)
        session.answers["q_tier"] = AnswerItem(question_id="q_tier", question_title="Tier", answer="PoC")
        
        brd = generate_brd(session)
        assert brd.client_name == client
        assert len(brd.technical_components) == 6
        assert len(brd.sizing_bom) >= 5
        assert brd.role_efforts is not None and len(brd.role_efforts) == 12
        assert len(brd.project_phases) == 18
        assert brd.total_person_days > 0
        assert brd.total_labour_cost_usd > 0
        assert brd.schedule_feasibility is not None
